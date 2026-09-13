"""Owned, idempotent 4 MiB upload parts. Final media still uses the existing GridFS finalizer."""
import hashlib
import os
import tempfile
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

CHUNK_BYTES = 4 * 1024 * 1024


def now():
    return datetime.now(timezone.utc)


class UploadInit(BaseModel):
    upload_id: UUID
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(max_length=100)
    size: int = Field(gt=0)


class UploadState(BaseModel):
    upload_id: str
    status: str
    chunk_size: int = CHUNK_BYTES
    total_chunks: int
    received: list[int] = Field(default_factory=list)
    media_id: str | None = None
    size: int
    processing: bool = False
    deduped: bool = False


class PartResult(BaseModel):
    index: int
    received: bool = True


async def setup_upload_indexes(db):
    # Parts have their OWN expiry: removing a session must never leave orphan bytes.
    for name in ('media_uploads', 'upload_stage.chunks'):
        await db[name].create_index('expires_at', expireAfterSeconds=0)
    await db.media_uploads.create_index([('user_id', 1), ('status', 1)])


def create_upload_router(db, get_user, store_file, max_size, quota_info, storage_used, quotas):
    router = APIRouter(prefix='/media/uploads')
    sessions, parts = db.media_uploads, db['upload_stage.chunks']

    async def owned(upload_id, user):
        doc = await sessions.find_one({'_id': str(upload_id), 'user_id': user['user_id'],
                                       'expires_at': {'$gt': now()}})
        if not doc:
            raise HTTPException(404, 'Envoi expiré ou introuvable')
        return doc

    async def state(doc):
        result = doc.get('result') or {}
        received = await parts.find({'files_id': doc['_id']}, {'_id': 0, 'n': 1}).sort('n', 1).to_list(doc['total_chunks'])
        return UploadState(upload_id=doc['_id'], status=doc['status'],
                           total_chunks=doc['total_chunks'], size=doc['size'],
                           received=[x['n'] for x in received],
                           media_id=result.get('media_id'), processing=bool(result.get('processing')),
                           deduped=bool(result.get('deduped')))

    @router.post('', response_model=UploadState)
    async def init(body: UploadInit, user: dict = Depends(get_user)):
        if body.size > max_size:
            raise HTTPException(413, f'Fichier trop lourd (max {max_size // 1_000_000} Mo)')
        key = str(body.upload_id)
        existing = await sessions.find_one({'_id': key})
        if existing:
            existing = await owned(key, user)
            if existing['size'] != body.size or existing['filename'] != body.filename:
                raise HTTPException(409, 'Cet envoi correspond à un autre fichier')
            return await state(existing)
        used = await storage_used(user['user_id'])
        active = await sessions.find({'user_id': user['user_id'], 'status': {'$ne': 'complete'},
                                      'expires_at': {'$gt': now()}}, {'_id': 0, 'size': 1}).to_list(8)
        if len(active) >= 8:
            raise HTTPException(429, 'Trop d’envois en attente — termine ou annule un envoi')
        if used + sum(x['size'] for x in active) + body.size > quotas[quota_info(user)['tier']]:
            raise HTTPException(413, 'Stockage disponible insuffisant pour cet envoi')
        doc = {'_id': key, 'user_id': user['user_id'], 'filename': body.filename,
               'content_type': body.content_type, 'size': body.size,
               'total_chunks': (body.size + CHUNK_BYTES - 1) // CHUNK_BYTES,
               'status': 'uploading', 'expires_at': now() + timedelta(hours=24)}
        try:
            await sessions.insert_one(doc)
        except DuplicateKeyError:
            doc = await owned(key, user)
        return await state(doc)

    @router.get('/{upload_id}', response_model=UploadState)
    async def status(upload_id: UUID, user: dict = Depends(get_user)):
        return await state(await owned(upload_id, user))

    @router.put('/{upload_id}/chunks/{index}', response_model=PartResult)
    async def put(upload_id: UUID, index: int, request: Request, user: dict = Depends(get_user)):
        doc = await owned(upload_id, user)
        if doc['status'] != 'uploading':
            raise HTTPException(409, 'Envoi déjà en cours de finalisation')
        if index < 0 or index >= doc['total_chunks']:
            raise HTTPException(416, 'Numéro de bloc invalide')
        expected = min(CHUNK_BYTES, doc['size'] - index * CHUNK_BYTES)
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > expected:
                raise HTTPException(413, 'Bloc trop volumineux')
        if len(data) != expected:
            raise HTTPException(400, 'Bloc incomplet')
        digest = hashlib.sha256(data).hexdigest()
        key = f'{upload_id}:{index}'
        try:
            await parts.insert_one({'_id': key, 'files_id': str(upload_id), 'n': index,
                                    'data': bytes(data), 'sha256': digest, 'expires_at': doc['expires_at']})
        except DuplicateKeyError:
            old = await parts.find_one({'_id': key}, {'_id': 0, 'sha256': 1})
            if not old or old['sha256'] != digest:
                raise HTTPException(409, 'Le bloc reçu est différent du bloc sauvegardé')
        return PartResult(index=index)

    @router.post('/{upload_id}/complete', response_model=UploadState)
    async def complete(upload_id: UUID, user: dict = Depends(get_user)):
        doc = await owned(upload_id, user)
        if doc['status'] == 'complete':
            return await state(doc)
        indexes = await parts.find({'files_id': str(upload_id)}, {'_id': 0, 'n': 1}).sort('n', 1).to_list(doc['total_chunks'] + 1)
        if [x['n'] for x in indexes] != list(range(doc['total_chunks'])):
            # Another completion may have committed and removed its staged bytes
            # between our session read and part query. Return that stable result.
            latest = await owned(upload_id, user)
            if latest['status'] in ('complete', 'finalizing'):
                return await state(latest)
            raise HTTPException(409, 'Il manque des blocs — reprends l’envoi')
        claimed = await sessions.update_one(
            {'_id': str(upload_id), 'user_id': user['user_id'], '$or': [
                {'status': 'uploading'}, {'status': 'finalizing', 'lease_until': {'$lt': now()}}]},
            {'$set': {'status': 'finalizing', 'lease_until': now() + timedelta(minutes=5)}})
        if not claimed.modified_count:
            return await state(await owned(upload_id, user))
        try:
            with tempfile.TemporaryDirectory(prefix='chunks_') as td:
                path = os.path.join(td, 'media.bin')
                length = 0
                with open(path, 'wb') as out:
                    async for part in parts.find({'files_id': str(upload_id)}, {'_id': 0, 'data': 1, 'sha256': 1}).sort('n', 1).batch_size(1):
                        data = part['data']
                        if hashlib.sha256(data).hexdigest() != part['sha256']:
                            raise HTTPException(422, 'Intégrité du bloc invalide')
                        out.write(data); length += len(data)
                if length != doc['size']:
                    raise HTTPException(409, 'Envoi incomplet')
                result = await store_file(user, path, doc['filename'], doc['content_type'])
            await sessions.update_one({'_id': str(upload_id)}, {'$set': {'status': 'complete', 'result': result}, '$unset': {'lease_until': ''}})
            await parts.delete_many({'files_id': str(upload_id)})
            return await state(await owned(upload_id, user))
        except Exception:
            await sessions.update_one({'_id': str(upload_id), 'status': 'finalizing'}, {'$set': {'status': 'uploading'}, '$unset': {'lease_until': ''}})
            raise

    @router.delete('/{upload_id}', response_model=PartResult)
    async def cancel(upload_id: UUID, user: dict = Depends(get_user)):
        doc = await owned(upload_id, user)
        if doc['status'] == 'finalizing':
            raise HTTPException(409, 'Finalisation en cours')
        await parts.delete_many({'files_id': str(upload_id)})
        await sessions.delete_one({'_id': str(upload_id), 'user_id': user['user_id']})
        return PartResult(index=-1)

    return router