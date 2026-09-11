# PRD — BEATCUT

## UX (5 sept 2026) — Série optimisée mobile (v13.23-serie-mobile)
- ✅ Tuiles de styles : carrousel horizontal snap (flex 44%/150 px min, hauteur 132 px, sélection accent + glow), scrollbar masquée
- ✅ Aperçus de l'étape 2 : carrousel swipable (cartes 80 % de large, snap center, canvas pleine largeur, boutons 44 px), hint « Fais défiler pour comparer » (mobile only, traduit)
- ✅ Bouton « Exporter la sélection » sticky en bas (safe-area) ; testé visuellement mobile 390 px (config + review simulée)

## Feature (5 sept 2026) — Bouton Série dans « Plus » mobile
- ✅ `#mobMore` : bouton « Série de vidéos » (`mob-serie-btn`) → ferme la feuille + `go('serie')` ; testé mobile 390 px (navigation #/serie OK)

## Fix (5 sept 2026) — Sélecteur de clips du plan (v13.22-pickclip)
- ✅ « Remplacer le clip » n'affichait visuellement qu'un seul clip : les clips sans vignette étaient des carrés sombres invisibles + `thumbs[0]` pouvait être vide alors que d'autres slots avaient une vignette
- ✅ Corrigé : première vignette non vide (`find(Boolean)`), clip actuel bordé accent, clips sans vignette affichent leur nom sur fond clair — testé : 6 clips → 6 tuiles visibles (mobile 390 px)

## UX (4 sept 2026) — Bande de scrub timeline (v13.21-scrub)
- ✅ Nouvelle bande de scrub dédiée (`#tlRuler`) au-dessus des pistes : 26 px desktop / 36 px mobile, pleine largeur, curseur ew-resize, hover teinté
- ✅ Drag continu : pointer capture, aperçu mis à jour en direct (rAF), reprise auto de la lecture au relâcher si elle tournait ; clic simple conservé sur les pistes
- ✅ Poignée ronde sur la tête de lecture (::before 15 px desktop / 19 px mobile) dans la bande
- ✅ Hauteurs de grille ajustées (+26/+36 px) aux 3 breakpoints pour ne rien rogner ; testé visuellement desktop + mobile 390 px

## Fix Firefox (3 sept 2026) — v13.20-ff
Reproduction en vrai Firefox (Playwright) : `wcFail` immédiat + chaîne <video> fragile. Correctifs :
- ✅ **Timeline aux vignettes identiques** : `makeThumbsTag` ne purgeait pas le cache `_timgs` → corrigé (la timeline se met à jour comme la banque)
- ✅ **Firefox : play() peut ne jamais se résoudre & rVFC peut ne pas tirer sur vidéo en pause** → courses avec timeout (350 ms / 300 ms) dans seedThumbs + makeThumbsTag ; `v.load()` explicite dans tagMeta
- ✅ **Lecture de secours `<video>` natif** (`liveTagFrame`) quand WebCodecs KO : seek/play du clip.el et dessin par rAF, activé UNIQUEMENT si `_wcFail` (Chrome inchangé) ; pause auto à l'arrêt/changement de plan. Validé en scrub FF (frames réelles, temps différents = images différentes)
- ✅ **MIME normalisé** dans addClip (File sans type → déduit de l'extension ; FF exige un type sur les blobs vidéo)
- ✅ **Backend 500 /thumbs** : le nettoyage GridFS purgait les sprites (`thumbs_of` non épargné) → épargnés désormais + endpoint auto-répare les références cassées (unset + régénération)
- ✅ Tests : FF vignettes 4/4 distinctes en 2,5 s ; pire cas Chromium sans H.264 → vignettes OK via sprite serveur ; lecture Chrome 60 fps sans régression. Projet démo nettoyé des clips de test.

## Perf (3 sept 2026) — Fluidité de l'aperçu (v13.19-fluid)
Recherche best practices éditeurs en ligne (WebCodecs pipeline, CapCut/Clipchamp) puis application :
- ✅ **Zéro travail lourd pendant la lecture** : thumbDoctor en pause, `_wcMakeThumbsNow` attend l'arrêt (entrée + à chaque itération), `ensureClipProxy` ne démuxe jamais pendant la lecture, `renderClips()` des vignettes différé (`_uiDirty` vidé au stop)
- ✅ **Résolution adaptative façon CapCut** : `setPreviewScale()` — fenêtre FPS de 2 s ; <22 fps → 0.75×, <15 fps → 0.5× ; retour à 1× au stop (l'export reste pleine résolution)
- ✅ **Tampons décodeur élargis** : 10→14 frames, decodeQueue 14→18, pompe 20→15 ms
- ✅ Testé E2E : lecture réelle 60 fps, aucun stall, scale=1 sur machine rapide, restauration au stop, aucune erreur JS

## Refonte (31 août 2026) — brat en layout flux (v13.18-brat-flow)
- ✅ Étude des « brat generators » (bratify, epitrite) : le vrai effet = bloc compact aligné à gauche, minuscules, graisse 700, mots révélés un par un
- ✅ Le mode spread/brat abandonne les ancres fixes gauche/centre/droite (source des chevauchements) pour un **layout en flux mesuré** : chaque mot placé après le précédent avec espace réel, wrap auto à 84% de largeur → chevauchement impossible par construction
- ✅ Layout calculé sur le groupe entier → position stable pendant la révélation ; règle d'effacement 0,45 s après fin de phrase conservée
- ✅ Preset brat passé en weight:700, shadow:4 ; validé visuellement sur canvas isolé (1/3/6 mots, fond vert brat)

## Fix (31 août 2026) — brat : chevauchements + réapparition (v13.17-brat-fit)
- ✅ Anti-chevauchement : mesure des mots de chaque ligne et réduction auto de la police (`k=min(1, dispo/besoin)`) pour respecter les ancres gauche/centre/droite quelle que soit la taille de police
- ✅ La phrase terminée disparaît 0,45 s après son dernier mot si le mot suivant appartient à un nouveau groupe (plus de réapparition entière pendant les silences)
- ✅ Validé : canvas isolé avec mots longs à police 1,25× (aucun chevauchement) + 0 pixel de texte après le silence

## Feature (31 août 2026) — Mode « brat » (v13.16-brat)
- ✅ L'option d'affichage « Étalé » renommée **« brat »** (bouton Affichage + nom du preset)
- ✅ Les mots gardent leur emplacement étalé mais apparaissent désormais **un par un** (cumulatif jusqu'au mot chanté), au lieu de tous d'un coup — filtre `li*6+ri*3+i2>idx` dans le rendu spread de `drawLyricBlock`
- ✅ Vérifié numériquement : pixels de texte strictement croissants aux 4 timestamps des mots (preview et export partagent le même rendu)

## Fix (30 août 2026) — Détection des paroles fiabilisée (v13.15-lyrics-fix)
- ✅ **Blocage étape 1→2** : tous les fetch de la détection (acapella POST/polls/résultat, transcription) ont désormais un timeout dur (`API._fetchT`) — un appel réseau ne peut plus rester suspendu indéfiniment. Un poll raté n'est plus fatal (retente au tour suivant). Plafond global acapella 5 min. Transcription : 1 réessai automatique.
- ✅ **Mauvaise langue** : sélecteur "Langue des paroles" (fr/en/es/de/it/pt/ar/auto, persisté `bc_lyr_lang`, défaut = langue de l'UI) transmis à Whisper. Backend : whitelist regex du code langue + temperature 0.
- ✅ Testé : curl transcribe avec language=fr → "French" forcé ; langue invalide ignorée (200) ; sélecteur visible et fonctionnel (screenshot).
- ✅ **Refactor stockage transitoire** (lint deploy) : `/api/separate` envoie l'audio en mémoire (BytesIO) directement à Replicate (plus d'écriture pod, testé E2E : job done en 45 s) ; `/api/export/finalize` : FFmpeg lit directement les fd Starlette via `/proc/self/fd/N` + `pass_fds` (zéro copie disque des uploads, sortie via FileResponse+BackgroundTask ; testé : mp4 h264+aac ✓).

## Fix (24 août 2026) — UI recadrage
- ✅ Les contrôles de recadrage (Zoom/Centrer/Terminé) ne couvrent plus la vidéo : astuce en haut de l'aperçu + barre compacte fixée en bas de l'écran (`#cropBar`, position:fixed). Validé par screenshot.

## Implémenté (23 août 2026) — Vignettes SERVEUR FFmpeg (modèle veed.io, choix utilisateur "option a")
- ✅ **Backend** : à chaque upload vidéo (upload direct, import Pexels, import lien), FFmpeg génère une **bande filmstrip JPEG** (16 frames si ≤40s, sinon 24, 180×240 chacune) depuis le fichier disque (zéro course avec le transcodage) → GridFS (`metadata.thumbs_id`, marquée `is_proxy` pour être exclue des quotas/listes)
- ✅ Endpoint `GET /api/media/{id}/thumbs` : 200 image/jpeg + headers `X-Thumb-Count`/`X-Thumb-Duration` ; 202 pendant génération ; 404 si non-vidéo/échec ; génération à la demande (`_auto_thumbs`) pour les vieux médias
- ✅ Fix course transcodage : `_transcode_media` relit les métadonnées fraîches avant re-upload (ne perd plus `thumbs_id`)
- ✅ **Studio** (`v13.14-srvthumbs`) : `serverThumbs()` télécharge la bande (~150 Ko) et `applySpriteThumbs()` la découpe par sous-plan — remplace posters/slots vides, jamais une vraie vignette WC. Hooks : addClip, startClipUpload, startPexelsImport, makeThumbs, makeThumbAt, thumbDoctor
- ✅ **Codec-agnostique** : si WebCodecs ET `<video>` échouent (HEVC iPhone, headless…), les `seeks` sont synthétisés depuis `X-Thumb-Duration` → vignettes garanties même si le navigateur ne sait pas décoder la vidéo
- ✅ Tests : backend 4/4 pytest (`/app/backend/tests/test_srv_thumbs.py`), E2E studio validé (upload → 4 vignettes réelles en ~2,5 s, iteration_30 + retest playwright)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Problème original
"Voici mon site en version html copie le et fais en un vrai site fonctionnel qui a une belle page d'accueil un système pour se désabonner une DA plus pro et propre et faire en sorte qu'il soit fonctionnel sur mobile et sur pc."
Fichier fourni : `beatcut.html` — studio de montage beat-sync 100% client-side (BPM auto, cuts sur le beat, paroles IA Whisper, 8 styles de sous-titres, effets VHS/glitch, export mp4 9:16).

## Choix utilisateur
- Auth : email/mot de passe (JWT) ET Google (Emergent-managed) — les deux
- Paiement : Stripe mode test (sk_test_emergent), abonnement PRO 9,99 €/mois + bouton "Se désabonner"
- Studio : conservé intégralement, intégré au nouveau site
- DA : garder les couleurs (noir #121016 / ivoire #ece6da / rouge #ff3b30 / vert OSD #d9ffd0) mais plus propre et moderne

## Architecture
- **Backend** FastAPI + MongoDB (`/app/backend/server.py`) : auth JWT (cookies httpOnly) + sessions Google Emergent, Stripe via emergentintegrations, collections `users`, `user_sessions`, `login_attempts`, `payment_transactions`
- **Frontend** React + Tailwind + shadcn (`/app/frontend/src`) : Landing, AuthPage (login/register), Dashboard (abonnement + désabonnement), Studio (iframe)
- **Studio** : `/app/frontend/public/studio.html` — l'app originale adaptée (Supabase retiré, auth via `/api/auth/me`, watermark gratuit conservé, bouton PRO → /dashboard?upgrade=1)
- Fonts : Cabinet Grotesk (display), DM Sans (body), JetBrains Mono (OSD)

## Modèle d'abonnement
- Stripe RÉEL (clé sk_live du client) : checkout en mode `subscription` 12,99 €/mois récurrent
- Renouvellement automatique géré par Stripe ; synchronisé par polling (`sync_stripe_subscription` sur /auth/me)
- "Se désabonner" → `cancel_at_period_end=True` côté Stripe, accès conservé jusqu'à fin de période
- "Se réabonner" → réactivation Stripe si encore en période, sinon nouveau checkout

## Séparation voix/instru (acapella)
- **Replicate** + modèle **Demucs v4 (htdemucs)** via `cjwbw/demucs` — GPU à la demande, pay-per-use (~0,01-0,02 € par séparation)
- Scale-to-zero : aucun coût quand personne ne sépare
- Endpoint asynchrone : POST /api/separate → job_id, GET /api/separate/{id} statut, GET /api/separate/{id}/result wav
- Réservé aux abonnés PRO (403 sinon)

## Implémenté (12 juin 2026)
- ✅ Landing page FR responsive (hero, marquee, 6 features, 4 étapes, tarifs Gratuit/PRO, CTA, footer)
- ✅ Auth complète : register/login email+mdp, Google OAuth (Emergent), logout, routes protégées, brute force (X-Forwarded-For)
- ✅ Mot de passe oublié : /forgot-password + /reset-password (token 1h, usage unique) — emails simulés tant que RESEND_API_KEY vide (lien affiché à l'écran)
- ✅ Stripe LIVE récurrent : checkout subscription, annulation réelle, réactivation, sync renouvellement, transactions idempotentes
- ✅ Emails transactionnels (structure Resend prête : reset, confirmation PRO, confirmation annulation) — mode simulé en attendant le domaine
- ✅ Proxy clé-en-main : /api/proxy/pexels + /api/proxy/transcribe (clés Pexels/Groq côté serveur, champs masqués dans le studio)
- ✅ Dashboard : badge plan, Passer en PRO, Se désabonner (AlertDialog), Se réabonner, infos compte
- ✅ Studio intégral intégré (iframe), watermark gratuit / export PRO, lien retour compte
- ✅ Tests E2E itération 2 : backend 24/24, frontend 100%

## Implémenté (24 juin 2026)
- ✅ **6 nouveaux presets de sous-titres dynamiques** dans le Studio :
  - **TIKTOK NEON** : mot par mot, couleurs arc-en-ciel pulsantes + halo néon
  - **WORD POP 3D** : ombre stack 3D extrudée + rotation + scale sur le beat
  - **HANDWRITE** : écriture manuscrite révélée gauche-droite + trait fluo sous le mot
  - **BOUNCE RAINBOW** : chaque mot rebondit dans une couleur différente
  - **CINÉMA** : barres noires + sous-titre épuré centré (look pro/film)
  - **BIG IMPACT** : un mot massif occupe tout, drop shadow brutal, tilt et couleurs variables
- ✅ **9 nouvelles polices** ajoutées au dropdown (Anton, Bangers, Bungee, Righteous, Fredoka, Luckiest Guy, Permanent Marker, Rubik Mono One, Press Start 2P)
- ✅ **Texte derrière le sujet (IA)** : MediaPipe Selfie Segmentation chargé à la demande, masque la silhouette de la personne et réinjecte au-dessus du texte → le sous-titre passe DERRIÈRE le sujet
- ✅ Toggle "Derrière le sujet" dans la section Sous-titres, chargement lazy de l'IA au premier clic

## Corrections (juillet 2026)
- ✅ **Upload MP3 mobile (iOS Safari)** : suppression de l'attribut `accept` sur audioInput/clipInput/acapInput — iOS grisait les MP3 de l'app Fichiers. Validation 100% JS avec message d'erreur clair.
- ✅ **Séparation acapella cassée en PRODUCTION** : les jobs étaient stockés dans `SEP_JOBS` (dict en mémoire) → en prod multi-workers, le GET statut tombait sur un autre worker → "Job introuvable". Fix : jobs stockés dans MongoDB (`separation_jobs`), résultat streamé depuis l'URL Replicate via StreamingResponse. Testé E2E sur preview (job done en ~12s, WAV 529 Ko téléchargé).
- ⚠️ Ces correctifs nécessitent un REDÉPLOIEMENT pour être actifs sur beat-cut.com

## Implémenté (6 juillet 2026) — Plan BASIC 6,99 €
- ✅ **Nouveau plan BASIC** : 6,99 €/mois — export sans watermark, 10 vidéos/mois, sous-titres .srt, SANS acapella
- ✅ Backend : `sub_info` renvoie `tier` (free/basic/pro), checkout Stripe plan basic (699 cents), quota mensuel via `export_logs` MongoDB (`POST /api/export/register` → 429 au-delà de 10, `GET /api/export/quota`), acapella verrouillée PRO only (403 pour Basic), annulation auto de l'ancien abonnement Stripe en cas d'upgrade Basic→PRO, MRR admin inclut les basic
- ✅ Studio : export compté pour Basic (message "Export X/10 ce mois-ci"), overlay upgrade si quota atteint, acapella bloquée pour Basic (requireProPlan), auto-extraction acapella réservée tier pro
- ✅ Landing : 4 cartes tarifs (Gratuit / BASIC "NOUVEAU" / PRO "RECOMMANDÉ" / PRO Annuel) + **tableau comparatif** 9 fonctionnalités × 3 plans
- ✅ Dashboard : badge BASIC, barre de progression quota X/10, bouton "Passer en PRO" (remplace l'abonnement Basic), 3 boutons d'offres pour les comptes gratuits
- ✅ Tests : 17/17 backend (pytest `/app/backend/tests/test_basic_plan.py`), frontend 100% (iteration_3.json)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com
- ℹ️ Compte demo@beatcut.fr configuré en plan Basic (test)

## Implémenté (7 juillet 2026) — Admin enrichi
- ✅ **MRR hors promos** : seuls les abonnés avec un vrai `stripe_subscription_id` actif comptent dans le MRR (les accès offerts via code promo sont exclus)
- ✅ **Compteur "Payants réels (Stripe)"** vs "Actifs via promo / offert" dans les stats admin
- ✅ **Liste complète de tous les inscrits** (`GET /api/admin/users`) : email, plan (badge coloré), payant ✓/offert, code promo utilisé, provider, date — table scrollable
- ✅ Bouton **"Copier tous les emails"** (presse-papier, pour newsletters)
- ✅ Nettoyage : 35 comptes de test résiduels supprimés de la DB preview
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Implémenté (9 juillet 2026) — V2 COMPLÈTE (fichier fourni par Jules) — testé 100% (iteration_6)
### Studio V2 (`/app/frontend/public/studio.html`, ancien sauvegardé en studio-v1-backup.html)
- ✅ Nouvelle DA « encre bleutée + LED rouge » (Bricolage Grotesque/Inter/JetBrains Mono), SPA hash-routing (#/accueil, #/morceaux, #/edit/{id})
- ✅ **Toutes les APIs branchées** : auth réelle (/api/auth/me, avatar→/dashboard, redirect /login), plan+quota serveur, transcription Groq (/api/proxy/transcribe), acapella Replicate PRO (/api/separate), banque Pexels (UI de recherche ajoutée), upload/download GridFS
- ✅ **Morceaux cross-device** : store localStorage remplacé par /api/projects (bootRemote, persistRemote débounce 800ms, loadRemoteMorceau restaure audio GridFS + clips + paroles + style + extrait + BPM), suppression serveur avec bouton ✕
- ✅ Paroles : détection réelle (acapella si PRO → transcribe), « Coller mes paroles » avec remap LCS (remapPasted), « Recaler » réel
- ✅ Export : quota serveur vérifié AVANT, décompte APRÈS succès réel (/api/export/register)
- ✅ Garde beforeunload pendant l'upload audio ; window.API exposé pour les tests
### Nouvelle règle de quota export
- ✅ **GRATUIT = 1 export découverte AU TOTAL (lifetime), SANS watermark** (CDC §1) ; Basic = 10/mois ; Pro = illimité. Backend /api/export/register + /api/export/quota mis à jour (tests pytest adaptés)
### Landing + Profil nouvelle DA
- ✅ index.css : tokens globaux V2 (fond #0E1116, panel #151A21, accent #FF453A, radius 12px) → TOUTES les pages React héritent (Dashboard, Admin, Auth, Projects)
- ✅ Landing réécrite « simple » : hero waveform LED, 4 étapes, 4 cartes tarifs, tableau comparatif compact, CTA final
### Dette technique (iteration_6)
- Extraire js/{api,store,audio,subs}.js de studio.html ; data-testid manquants dans le studio V2 ; AbortController polling acapella ; retry persistRemote hors-ligne ; filtre mots fantômes transcription
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com
- ℹ️ NOTE : le phasage CDC (P1 Express, P3 styles/créateur, LOT 5) est en partie couvert par la V2 de Jules (pages, éditeur, presets, créateur de style local). Les quotas journaliers du CDC §1 (détections IA/jour, recherches clips/jour, acapella 20/j) restent À FAIRE côté serveur.

## Cahier des charges V2 (reçu 8 juillet 2026) — décisions de Jules
- Export découverte Gratuit (1 au total) : SANS watermark
- Stockage complet des médias pour les projets (LOT 4) : OUI dès l'implémentation
- Phasage : LOT 0 (bug synchro) ✅ → P2 (LOT 4 Projets ✅ puis LOT 2 Timeline ✅) → P1 (quotas + Express) → P3 (Styles + créateur) → LOT 5 transverse

## Implémenté (8 juillet 2026) — P2 : LOT 4 Projets + LOT 2 Timeline
### LOT 4 — Projets (CDC §6) — testé 42/42 backend + frontend 100% (iteration_4)
- ✅ Stockage médias **GridFS** (bucket `media`) : POST /api/media/upload (dédup sha256, max 80 Mo), GET /api/media/{id} (stream, sécurisé par user), GET /api/media/quota. Quotas stockage : 200 Mo free / 2 Go basic / 10 Go pro
- ✅ CRUD projets : POST /api/projects (upsert), GET liste/détail, duplicate, DELETE avec purge des médias orphelins. Quotas projets : 1 free / 10 basic / illimité pro (429 + invite upgrade)
- ✅ Studio : serializeProject/restoreProject (audio + clips perso GridFS + clips Pexels par URL + paroles + timings + style + réglages), auto-save 30 s, badge « Enregistré ✓ », upload médias en tâche de fond, ouverture via /studio?project=ID
- ✅ Page React « Mes projets » (/projects) : cartes vignette, renommer, Ouvrir/Dupliquer/Supprimer, lien navbar desktop+mobile
### LOT 2 — Timeline (CDC §4) — testé 100% frontend (iteration_5)
- ✅ 2 pistes : CLIPS (segments aimantés au beat, couleur par clip) + MOTS (libres)
- ✅ Bottom sheet segment : choix du clip (vignettes vidéo), point d'entrée (slider), 🔒 verrouiller
- ✅ state.cutOv : les segments verrouillés **survivent au 🎲 Re-tirer** ; sérialisé dans les projets
- ✅ Piste MOTS : drag des bords (timings) et déplacement, double-clic pour corriger (vide = supprimer), adoption des units comme anchors 'manual', subs.raw reconstruit
- ✅ Zoom +/−, règle graduée par beat, playhead sync lecture, seek au clic
### Dette technique notée (pour lots suivants)
- studio.html = 3546 lignes → extraire timeline.js ; bindWordDrag → AbortController ; renderTimeline → debounce rAF ; cutOv indexé par index (fragile si bpm/trim changent → indexer par timestamp) ; server.py 1560 lignes → modules
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Implémenté (8 juillet 2026) — LOT 0 : synchro sous-titres
- ✅ **`remapWords` (LCS) vérifié** : la fonction d'origine EST conservée et fonctionne (preview ET prod). 11 tests unitaires couvrant les critères 2.5 du CDC (1 mot corrigé sur 50 → 49 timestamps strictement identiques ; insertion locale ; suppression sans impact ; 30% mots différents calés ; ponctuation/casse ignorées). Test permanent : `/app/frontend/tests/test_remap_words.js`
- ✅ **Mode « Colle tes paroles »** (CDC §2.4) : bouton « 📋 J'ai mes paroles — les coller » + modal. Si grille temporelle déjà détectée → calage immédiat via remapWords ; sinon → détection IA lancée automatiquement puis texte officiel posé sur les timings. Testé e2e (mots identiques = timestamps exacts, verlan/argot interpolés localement)
- ✅ **Garde-fou mode Beats** : avertissement si l'utilisateur bascule en "Beats" avec des mots calés IA (source de désync accidentelle)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Comptes seedés
Voir `/app/memory/test_credentials.md` (admin@beatcut.fr, demo@beatcut.fr)

## Backlog priorisé
- **P1** : Activer Resend dès que le domaine est prêt (remplir RESEND_API_KEY + SENDER_EMAIL dans backend/.env, redémarrer le backend — rien d'autre à faire)
- **P1** : Configurer le webhook Stripe dans le dashboard (endpoint /api/webhook/stripe, remplir STRIPE_WEBHOOK_SECRET) pour une synchro instantanée des renouvellements
- **P2** : Historique des paiements dans le dashboard ; page admin
- **P2** : Galerie de vidéos exportées (object storage) ; serveur d'extraction acapella (UVR)
- **P2** : Tester perfs MediaPipe sur mobile (Safari iOS / Chrome Android) — peut être lourd pour les vieux appareils
- **P3** : Tester l'export MP4 avec "Derrière le sujet" actif (vérifier que le MediaRecorder capture bien la composition)

## Notes
- ⚠️ STRIPE EN MODE LIVE : tout paiement complété débite une vraie carte
- Les clés Groq/Pexels sont dans backend/.env, jamais exposées au navigateur
- Emails : mode simulé (logs serveur + lien affiché) tant que RESEND_API_KEY est vide

## Implémenté (9 juillet 2026) — Studio V2 : Pexels réel, édition paroles complète, barres IA, calage amélioré
- ✅ **Pexels branché** : suppression du listener mock « Banque de clips : à brancher par Emergent » — la recherche (Entrée) appelle le proxy `/api/proxy/pexels` réel, orientation suit le format vidéo, clic vignette = ajout du clip. Testé e2e (9 vignettes).
- ✅ **Synchro paroles éditeur ↔ timeline** : correction du conflit clic/double-clic (le re-render sur simple sélection cassait le dblclick) → `syncSel()` sans re-render. Double-clic (éditeur OU bloc timeline) = édition, propagée aux deux vues. Testé e2e.
- ✅ **Ajout de mots** : boutons « + » entre les chips (hover) avec timing auto dans le trou entre voisins ; double-clic sur zone vide de la piste paroles = mot à cet instant ; Escape/vide = annulation propre. Testé e2e.
- ✅ **Barres de chargement IA** (`aiBar`, haut de page, barre rouge + pastille) : détection paroles (progression acapella par polls + transcription), « Caler mes paroles », recalage, export vidéo (progression réelle s/s). Testé visuellement.
- ✅ **Calage auto amélioré** (`refineTimings`) : début de chaque mot aimanté sur l'attaque vocale (montée d'énergie ±140 ms de l'enveloppe), durées min 80 ms, micro-trous <150 ms comblés (anti-clignotement), zéro chevauchement. Appliqué à détection/coller/recalage. ⚠️ À valider à l'oreille avec un vrai morceau.
- ✅ Textes placeholders « EMERGENT : » nettoyés (paste hint, auth hint, commentaire format Pexels)
- ⚠️ Restant mocké dans studio.html : « Série de vidéos » (genSerie/exportKept — variantes non générées réellement)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Implémenté (9 juillet 2026) — Série de vidéos réelle (dernier bloc mocké branché)
- ✅ Flux : morceau (projets serveur chargés via GridFS + clips Pexels) → multi-sélection de styles (7 presets + styles perso ★) → N variantes réelles (paroles/timings conservés, plans re-tirés aléatoirement, styles round-robin, plans 🔒 respectés)
- ✅ Vignettes réelles (rendu canvas via `drawPreview(t, cvOverride)`) + bouton ▶ Aperçu (lecture audio + rendu variante en direct sur la carte)
- ✅ Export réel séquentiel des gardées : `exportVideo(nameSuffix)` promisifié, fichiers `Titre-vN.mp4`, quota décompté par vidéo, arrêt propre si quota atteint, style/plans du projet restaurés après la série
- ✅ Refactor : `fetchRemoteMorceau()` extrait de `loadRemoteMorceau` (réutilisé par la série), `presetDemoHTML()` partagé éditeur/série
- ✅ Testé e2e Playwright : génération 3 variantes (vignettes réelles vérifiées pixel), preview lecture start/stop, garder/jeter, export réel téléchargé (10 s), quota 10→9, restauration du style
- ℹ️ Fixture de test : projet « Morceau Série Test » sur le compte démo (audio WAV 12 s GridFS + clip Pexels + 6 mots)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Corrigé (10 juillet 2026) — Écrans noirs sur certains plans (aperçu + export)
- Cause : dans `drawPreview`, quand la vidéo d'un plan était en plein seek/décodage (`readyState<2`, `seeking`) ou mise en pause par le navigateur, RIEN n'était dessiné → fond noir avec paroles par-dessus
- ✅ Fallback en cascade : frame vidéo prête → vidéo ; sinon → **vignette du sous-plan** (Image mise en cache `clip._timgs`) ; sinon → dégradé. Plus jamais d'écran noir
- ✅ `wakeClips()` : relance `play()` sur les <video> en pause avant lecture, boucle extrait, aperçu série et export
- ✅ Testé : frame vidéo OK, branche vignette validée (thumb injecté rendu plein cadre), branche dégradé validée
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Corrigé (10 juillet 2026) — Plans pixelisés / qui ne se lancent pas (qualité vidéo 100%)
- Causes : (1) vignette de secours 90×120 upscalée en 1080×1920 = bouillie de pixels, affichée trop souvent ; (2) BUG re-seek en boucle : quand `seek + temps écoulé` dépassait la durée du clip, la comparaison sans modulo re-seekait à CHAQUE frame → plan bloqué en seeking, jamais net
- ✅ **Double lecteur par clip** (`cl.els[0/1]`, `poolEl`, `assignPlanPlayers` alternance par occurrence) : le plan suivant est pré-calé sur un 2e <video> en pause pendant que le courant joue → à la coupure, bascule sur un lecteur déjà prêt = image nette immédiate
- ✅ **Lookahead** dans `drawPreview` (pré-seek plan suivant + bouclage vers plans[0]) ; pause de l'ancien lecteur à la transition (`lastPlanEl`)
- ✅ **Fix modulo** : comparaison `|currentTime - target%duration|` → plus de re-seek infini
- ✅ **warmUpPlans(fromT)** : pré-cale les 2 premiers plans avant lecture/export (await dans exportVideo → 1re frame déjà nette) ; remplace wakeClips
- ✅ Vignettes de secours en **360×480** (4× plus nettes) — utilisées seulement quelques frames au pire
- ✅ Testé e2e (fixture WebM décodable en headless) : 5 s de lecture = 2 frames de secours sur ~300 (99,3 % vidéo native), pool 2 lecteurs OK, cas seek>durée : 5/20 au lieu de 20/20 bloqué
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Implémenté (10 juillet 2026) — Export "offline" WebCodecs + aperçu proxy (comme les logiciels de montage)
- ✅ **exportOffline** : rendu image par image (30 fps) — chaque frame attend le seek exact du clip (`seekPlanFrame`) avant d'être dessinée (`drawPreview(t, canvas offscreen pleine résolution)` avec flag `offlineRender`) puis encodée H.264 12 Mbps (`VideoEncoder avc1.640033`) + AAC 192k (`AudioEncoder`), muxé en MP4 via **mp4-muxer** (vendorisé : `/frontend/public/vendor/mp4-muxer.min.js`, global `Mp4Muxer`). Zéro freeze possible, qualité 100 % garantie, progression réelle en %
- ✅ **Dispatcher** `exportVideo` : quota/checks → `offlineSupported()` (isConfigSupported avc+aac) → offline, sinon `exportRealtime` (ancien MediaRecorder, conservé en repli). Échec offline → repli realtime automatique
- ✅ **Aperçu proxy demi-résolution** (`PREVIEW_SCALE=2`, canvas 540×960) : lecture beaucoup plus fluide ; `exportRealtime` repasse le canvas en pleine résolution pendant l'export puis restaure
- ✅ `drawPreview` : en mode offline, pas de play/lookahead/re-seek (le seek est géré par l'appelant)
- ✅ Testé : proxy 540×960 OK ; fallback realtime auto (pod headless sans encodeur H.264) avec export réel réussi + quota décompté + canvas restauré ; mécanique WebCodecs+muxer validée e2e (VP9/Opus, mêmes APIs, mp4 230 Ko généré)
- ℹ️ Le chemin offline H.264 s'active automatiquement sur Chrome/Edge/Brave/Android ; Safari sans AudioEncoder AAC → repli temps réel
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Corrigé (10 juillet 2026) — Freezes de l'aperçu : lecture événementielle (modèle V1 restauré)
- Cause : la V2 vérifiait la position vidéo À CHAQUE FRAME dans drawPreview (`|currentTime-target|>0.45 → seek`) → re-seeks en pleine lecture (drift audio/vidéo, boucles de clips) = micro-freezes. La V1 n'agissait qu'aux coupures
- ✅ Porté le modèle V1 : `syncLivePlan(t)` dans raf() détecte le changement de plan → `activatePlan(i)` (UNE fois par coupure) : play du lecteur pré-calé, pause de l'ancien, pré-seek du lecteur du plan suivant. `livePtr`/`liveEl` globaux, reset dans stopAll
- ✅ drawPreview en lecture : dessine `liveEl` tel quel, ZÉRO seek/play par frame. À l'arrêt (scrub) : calage à la demande conservé. Mode offline inchangé
- ✅ Aperçu série : `syncLivePlan` appelé dans la boucle withVariant
- ✅ Testé e2e : 60 fps constants, 6 seeks/5 s (= pré-calages aux coupures uniquement), 11 activations, lecteurs en pause au stop
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## URGENT corrigé (10 juillet 2026) — « Moteur vidéo des plans » (spec client appliquée à la lettre)
- ✅ 1. DOUBLE TAMPON : 2 <video> par fichier source (`poolEl`/`makePoolVideo`), plan N+1 pré-positionné en pause (`prepareNext`) pendant que N joue
- ✅ 2. À la coupure : permutation + play() UNIQUEMENT, zéro seek (`activatePlan`) ; pendant un plan (`ensureActive`) : re-seek seulement si dérive >0,9 s, paused→play(), ended→reprise au point d'entrée
- ✅ 3. Lecteur pas prêt : vignette 360×480 du plan, sinon dégradé — jamais de canvas vide
- ✅ 4. Éléments : muted, playsinline (+attribut), preload=auto, loop=false, disableRemotePlayback (addClip refactoré via makePoolVideo, plus de play() à l'import)
- ✅ 5. Export = même pipeline de rendu (offline: seekPlanFrame+drawPreview ; realtime: syncLivePlan dans raf) ; quota décompté seulement si fichier valide/complet (durée ≥ ext.dur−0,8 s en realtime ; offline complet par construction)
- ✅ BUG BONUS corrigé : retour sur un morceau distant déjà ouvert → resetAudioState purgait les médias sans re-téléchargement (_loaded restait true) → morceau vide. Fix : `M._loaded=false` au reset (openEditor + serieLoadMorceau)
- ✅ RECETTE exécutée (fixture « Recette 150BPM » id 032e4762018d45 : 150 BPM, 30 s, ~75 plans, 2 webm dont un GOP long -g 300 simulant les seeks lents) : 0 frame figée, 0 plan noir, 0 vignette sur 3 lectures d'affilée, 60 fps, seeks uniquement aux pré-calages, changement/retour morceau OK
- ⚠️ Non testable en headless (pas de codecs H.264/HEVC) : mp4 iPhone HEVC + H.264 GOP long → à valider par le client dans son navigateur
- 📋 PHASE SUIVANTE À CHIFFRER (demande client) : normalisation serveur à l'upload (transcode H.264 1080p max, GOP ~0,5 s, faststart)
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Implémenté (10 juillet 2026) — PHASE 1 : Transcodage serveur à l'upload + verrou de chargement (fix définitif freezes iPhone HEVC/4K)
- ✅ **Backend transcodage FFmpeg** (`imageio_ffmpeg`, sémaphore 2 jobs max) : `POST /api/media/upload` détecte les vidéos → réponse immédiate `{media_id, processing:true}` + tâche asyncio de transcodage → H.264 High 1080p max (grand côté 1920), **keyframes toutes les 0,5 s** (`force_key_frames`), AAC 128k stéréo, `+faststart`, yuv420p. Le fichier GridFS est REMPLACÉ avec le MÊME _id (références projets intactes). Échec ffmpeg → original conservé + `transcode_failed:true`
- ✅ `GET /api/media/{id}/status` → `{processing, transcoded, failed, size}` (scopé user, 404 autre user, 400 id invalide)
- ✅ **Migration admin** : `POST /api/admin/media/migrate` (lance en background sur toutes les vidéos GridFS non transcodées) + `GET` pour le statut `{running,total,done,failed}` — 403 non-admin. **Exécutée en preview : 7/7 vidéos migrées, 0 échec**
- ✅ **Frontend studio.html** : `API.uploadMedia` polle le statut (2 s × 150) ; `addClip` → badge « ⏳ Optimisation de ta vidéo… » (`data-testid=clip-optimizing-badge`) + une fois transcodé, `swapClipMedia` remplace le blob local par la version optimisée téléchargée ; échec → toast d'avertissement explicite
- ✅ **Verrous** : `play()`, `startLoop()`, `exportVideo()`, `genSerie()` bloqués avec toast tant qu'un clip s'optimise (`clipsOptimizing()`)
- ✅ **Verrou de chargement projet** : overlay plein écran `#loadOverlay` (`data-testid=load-overlay`) avec barre de progression réelle (streaming fetch + Content-Length) — audio + clips ENTIÈREMENT téléchargés en blobs avant ouverture de l'éditeur
- ✅ Testé : agent de test 10/10 backend (pytest `/app/backend/tests/test_media_transcode.py`) + e2e frontend complet (upload → badge → lecture bloquée → lecture OK après). Bench réel : 4K portrait 35 Mo → 1080×1920 2 Mo en ~3 s, keyframes exactes à 0,5 s
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com ; relancer la migration en prod après déploiement : `POST /api/admin/media/migrate` (connecté admin)
- 📋 Recommandations testeur (non bloquant, backlog) : endpoint `DELETE /api/media/{id}` ou GC des médias orphelins ; statut `queued` distinct si file d'attente transcode chargée

## Implémenté (10 juillet 2026) — Clips Pexels optimisés côté serveur (option A validée user)
- ✅ `POST /api/media/import-url` : le SERVEUR télécharge le clip Pexels (hosts *.pexels.com uniquement, https, max 80 Mo) puis le passe dans le même pipeline de transcodage (H.264, keyframes 0,5 s) → stocké GridFS, compte dans le quota user. Dédup sha256 conservée
- ✅ Refactor backend : `_store_media()` partagé entre `media_upload` et `media_import_url`
- ✅ **Fix upscale** : le filtre scale n'agrandit plus les vidéos < 1080p (`min(1920,iw)`) — un clip 720p reste en 720p (fichier plus léger). Testé : 720p in → 720p out
- ✅ Frontend : clic vignette Pexels → `API.importMedia` (zéro re-upload client) → poll statut → clip ajouté avec `mediaId` + `pexelsUrl` (les projets rechargent depuis GridFS en priorité). Toasts « ⏳ Optimisation du clip en cours… » / « ✓ Clip ajouté — optimisé »
- ✅ Testé e2e (curl + Playwright) : import Pexels 720p → transcodé en ~13 s, keyframes 0,5 s ; flux studio complet OK (recherche neon → clic → clip dans la banque en ~6 s)
- ℹ️ Les anciens projets avec clips Pexels (pexelsUrl seul) continuent de streamer depuis Pexels ; les nouveaux ajouts passent tous par GridFS optimisé
- ⚠️ Nécessite un REDÉPLOIEMENT pour beat-cut.com

## Corrigé (11 juillet 2026) — 🔴 Clients ayant payé sans recevoir leur accès Pro/Basic
- Cause : l'activation dépendait UNIQUEMENT du retour du client sur /dashboard?session_id=... après paiement Stripe. Onglet fermé / redirection ratée / cookie perdu (in-app browser iPhone) → paiement encaissé mais accès jamais activé. Webhook inactif (secret vide) = aucun filet
- ✅ **Réconciliation automatique** : `reconcile_payments()` (sessions non processed < 30 j → Stripe retrieve → si paid, `_claim_and_activate` idempotent + email de bienvenue) + `reconcile_subscriptions()` (vérifie statut/annulations/renouvellements auprès de Stripe, rafraîchit si synced_at > 12 h). Watchdog `_payments_watchdog()` lancé au startup, toutes les 10 min
- ✅ **Admin** : `POST /api/admin/payments/reconcile` (force la vérif de TOUS les abonnements) + section « Paiements & abonnements » dans /admin (bouton 🔁 Réconcilier + résultats détaillés avec emails activés et changements de statut)
- ✅ **Webhook Stripe auto-créé** : `POST /api/admin/payments/webhook-setup` crée l'endpoint via l'API Stripe pour le domaine courant (x-forwarded-host), secret stocké dans `db.config` (`_id: stripe_webhook`), cache mémoire. Handler `/api/webhook/stripe` : secret env prioritaire sinon db.config ; gère `checkout.session.completed`, `customer.subscription.updated/deleted`, `invoice.paid` (renouvellements + annulations instantanés). `GET /api/admin/payments/webhook` = statut
- ✅ Refactor : `_stripe_sub_status()` + `_apply_stripe_sub_state()` partagés (sync polling + webhook + réconciliation)
- ✅ Testé en preview : reconcile 4 sessions vérifiées (0 payées — normal, les vrais clients sont en base PROD) ; webhook créé sur le compte Stripe LIVE, signature vérifiée (400 payload non signé), puis endpoint preview SUPPRIMÉ du compte Stripe (nettoyage)
- ⚠️ **ACTIONS PROD après redéploiement** : (1) la réconciliation tourne toute seule dès le démarrage → clients réparés automatiquement ; (2) admin → « Réconcilier maintenant » pour vérifier immédiatement + voir les emails réparés ; (3) admin → « ⚡ Activer le webhook Stripe » UNE FOIS depuis beat-cut.com

## Corrigé (11 juillet 2026) — MRR admin juste vis-à-vis des vrais paiements
- Cause : le MRR était théorique (abonnés actifs en base locale × prix catalogue). Base locale incomplète (paiements non réclamés) → MRR faux
- ✅ `_stripe_revenue_stats()` : calcul direct depuis Stripe (source de vérité), cache 10 min — `stripe_mrr` (somme des abonnements actifs avec vrais montants, annuels prorata /12, coupons appliqués), `stripe_active_subs`, `revenue_this_month` + `revenue_total` (charges succeeded − remboursements)
- ✅ /admin : cartes « MRR RÉEL (STRIPE) », « ENCAISSÉ CE MOIS », « ENCAISSÉ TOTAL », « Abos Stripe actifs » (fallback sur le MRR estimé si Stripe indisponible)
- ✅ Vérifié en preview (même compte Stripe LIVE que la prod) : MRR réel 317,97 €, 29 abos actifs, 408,72 € encaissés — contre 0 € avec l'ancien calcul local. Confirme au passage l'ampleur du bug des accès non délivrés (29 abos Stripe vs 0 liés en base preview)

## Implémenté (11 juillet 2026) — Transcodage externalisé via Mux (fix des 10 min de transcodage en prod)
- Contexte : en prod (CPU limité), le transcodage FFmpeg local prenait ~10 min/vidéo. Choix user : externaliser avec Mux
- ✅ `_mux_transcode()` dans server.py : Direct Upload Mux (PUT serveur→Mux) → asset `video_quality: basic` (encodage GRATUIT, fallback `encoding_tier: baseline` si 400) + `max_resolution_tier: 1080p` + `static_renditions: highest` → poll asset ready + rendition MP4 → téléchargement `stream.mux.com/{playback_id}/highest.mp4` → **suppression de l'asset Mux** (finally, zéro stockage récurrent)
- ✅ `_transcode_media` : Mux d'abord, **repli FFmpeg local automatique** si Mux indisponible/échec. Tout le reste inchangé (statuts, badge studio, migration, import Pexels passent par le même chemin)
- ✅ Clés dans backend/.env : `MUX_TOKEN_ID`, `MUX_TOKEN_SECRET` (fournies par l'user)
- ✅ Testé e2e : 4K portrait 50 Mo → 1080x1920 H.264+AAC 2,1 Mo en ~35 s ; asset supprimé (204) ; 0 asset restant sur le compte Mux
- ⚠️ Compromis : keyframes Mux ~5 s (vs 0,5 s FFmpeg) — pas de contrôle GOP chez Mux. Le moteur double-lecteur pré-cale les seeks en avance → devrait rester fluide ; à valider par l'user. Option de repli si micro-lags : rendition 720p ou re-densification locale
- ⚠️ Nécessite un REDÉPLOIEMENT (+ les 2 clés Mux dans les env vars de prod si les .env ne sont pas repris automatiquement)

## Corrigé (12 juillet 2026) — Bugs iPhone Safari : export sans son, vignettes vides, export lent
- ✅ **Export sans son (Safari)** : flux MediaRecorder construit via `new MediaStream([videoTracks, audioTracks])` (addTrack sur le flux canvas fait perdre l'audio sur Safari) + mime `video/mp4;codecs=h264,aac` ajouté + `rec.start()` SANS timeslice sur Safari (le timeslice fragmente mal le MP4)
- ✅ **Vignettes vides** : (1) régénération des vignettes après `swapClipMedia` (elles étaient générées depuis l'original HEVC .mov indécodable puis jamais refaites) ; (2) `makeThumbs`/`makeThumbAt` : playsinline + nudge `play().then(pause)` + `v.load()` (iOS ne dessine pas les frames d'une vidéo jamais jouée) ; (3) même nudge dans `openPicker` (#pickVid)
- ✅ **Export lent (Safari)** : négociation multi-codecs AVC (`_avcCodec` : 640033→640028→4d4028→42e01f) dans offlineSupported/exportOffline → l'export rapide WebCodecs s'active sur Safari 26+ (AudioEncoder dispo depuis Safari 26). Sur iOS < 26 : reste en temps réel (limite navigateur, AudioEncoder absent — documenté)
- ✅ Non-régression Chrome : testing agent iteration_8 = 100 %, 0 erreur JS (export realtime 879 Ko téléchargé, vignettes webm régénérées, badge optimisation OK avec Mux ~23 s)
- ⚠️ Validation Safari iPhone par l'USER requise (impossible en headless) + REDÉPLOIEMENT nécessaire
- Notes testeur : env headless sans codecs h264 → tester les vignettes avec des WEBM (voir context_for_next_testing_agent d'iteration_8)

## Corrigé (12 juillet 2026) — Optimisation vidéo perçue comme trop longue (« 3 plombes »)
- Diagnostic chiffré (vidéo 45 s / 79 Mo) : PUT→Mux 6,6 s · encodage 2,2 s · rendition MP4 23,7 s (incompressible chez Mux) · download 6,7 s = ~41 s serveur + upload mobile client. Le vrai problème : TOUT était bloqué pendant ce temps
- ✅ **Optimisation non bloquante** : `clip._playable` (loadedmetadata + videoWidth>0) → la lecture/boucle n'est bloquée QUE si l'original est indécodable (`clipsBlocking()`), sinon montage + lecture immédiats avec l'original, remplacement silencieux à la fin (jamais en pleine lecture : attente `playing||looping`)
- ✅ Badge : overlay bloquant → petit chip discret `clip-opt-chip` (« ☁ Envoi X % » puis « ⏳ Optimisation en arrière-plan… ») quand le clip est lisible
- ✅ **Progression d'envoi réelle** : API.uploadMedia passé en XHR avec upload.onprogress (le % s'affiche dans le chip)
- ✅ Parallélisation : TRANSCODE_SEM 2→6 (Mux = network-bound, plusieurs clips uploadés d'affilée ne font plus la queue)
- ✅ Export/genSerie restent verrouillés pendant l'optimisation (l'export doit être parfait) avec message clair
- ✅ Testé e2e Playwright : chip non bloquant affiché, lecture démarrée PENDANT l'optimisation (tcNow avance), optimisation finie en ~18 s, badge disparu, vignettes régénérées
- ⚠️ REDÉPLOIEMENT nécessaire

## Implémenté (12 juillet 2026) — Export hybride Safari : rapide ET avec le son garanti
- Contexte : toujours pas de son en export sur iPhone (MediaRecorder Safari trop capricieux) + export temps réel trop lent. User ouvert à Mux/Replicate → impossible pour le rendu (paroles/effets = canvas client), solution retenue : **hybride client/serveur**
- ✅ `offlineSupported()` retourne désormais un mode : `'full'` (VideoEncoder+AudioEncoder → tout client, Chrome/Safari 26+), `'hybrid'` (VideoEncoder seul → Safari 16.4-25), `false` (→ realtime MediaRecorder)
- ✅ Mode hybride dans `exportOffline(nameSuffix, mode)` : vidéo encodée client (WebCodecs H.264, accéléré matériel iPhone, sans perte) → MP4 vidéo seule (mp4-muxer sans piste audio) → POST `/api/export/finalize` (vidéo + WAV stéréo `extractWavStereoBlob`) → serveur FFmpeg `-c:v copy -c:a aac 192k +faststart` → MP4 final téléchargé. **Son garanti à 100 %** (plus de MediaRecorder sur Safari moderne)
- ✅ Backend `POST /api/export/finalize` : auth, limites 500 Mo vidéo / 100 Mo audio, tmpdir, timeout 180 s. Testé : 6 s vidéo 1080x1920 + WAV → MP4 h264+AAC en **0,68 s** (copy vidéo = zéro ré-encodage)
- ✅ UI : étape « Ajout du son (serveur)… » dans la barre de progression
- ✅ Smoke test headless : 0 erreur JS, lecture OK, offlineSupported()=false en headless → repli realtime intact (testé iter_8)
- ⚠️ Le mode hybride ne peut PAS être testé en headless (pas de codecs H.264) — validation par l'USER sur iPhone requise
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (12 juillet 2026) — « Certaines vidéos ne sont pas sauvegardées »
- Cause : un clip n'est rattaché au projet QUE si l'upload serveur réussit. Échecs silencieux : fichier > 80 Mo (une vidéo iPhone 4K dépasse ça en ~1 min !), fermeture de la page avant la fin de l'envoi, stockage plein. Seul signal : un toast fugace
- ✅ Limite d'upload 80 → **300 Mo** (`MAX_MEDIA_SIZE`). Vérifié : l'ingress accepte 260 Mo en POST direct (200 OK, 7 s)
- ✅ Pré-contrôle taille côté client (`MAX_UPLOAD_MO=300`) avec message immédiat et explicite
- ✅ **Badge rouge persistant** « ⚠ Non sauvegardée — réessayer » (`data-testid=clip-save-failed-badge`, cliquable → `retryClipUpload` re-upload depuis le blob local) au lieu d'un toast éphémère
- ✅ Refactor : flux d'upload extrait dans `startClipUpload(clip, file)` (réutilisé par le retry)
- ✅ `beforeunload` : alerte navigateur si on ferme l'onglet pendant un envoi/optimisation (clips `_optimizing` ou `M._uploadingAudio`)
- ✅ Testé e2e Playwright : badge rouge rendu + cliquable, toast taille, 0 erreur JS. Fichiers de test GridFS supprimés
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (12 juillet 2026) — Clips Pexels passés au système non bloquant
- Avant : clic vignette Pexels → attente BLOQUANTE du transcodage serveur complet avant que le clip apparaisse
- ✅ Maintenant : clic → fetch direct du MP4 Pexels (~2 s) → clip utilisable/lisible IMMÉDIATEMENT → `startPexelsImport(clip)` en arrière-plan (import serveur + Mux) → swap silencieux + vignettes régénérées, même chip discret que les uploads perso
- ✅ Échec d'import silencieux : le clip reste référencé par son URL Pexels (comportement historique, pas de badge rouge)
- ✅ Bonus migration : à la réouverture d'ANCIENS projets, les clips Pexels sans mediaId déclenchent l'import en arrière-plan (condition dans addClip : `pexelsUrl && !mediaId`, indépendante de skipUpload) → migration douce vers GridFS
- ✅ Testé e2e : clip apparu en ~2 s, lecture pendant l'optimisation OK, 0 erreur JS
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (12 juillet 2026) — Son toujours absent des exports iPhone : audio 100 % serveur sur Safari
- Diagnostic factuel : export realtime reproduit en headless Chromium → le fichier CONTIENT une piste audio réelle (opus stéréo, max -2,9 dB) → notre code realtime est sain, le problème est exclusivement le MediaRecorder audio de Safari
- ✅ **Décision radicale : plus AUCUN chemin d'export Safari ne dépend de l'audio MediaRecorder** :
  - `exportRealtime` sur Safari : enregistre la VIDÉO SEULE (pas de piste audio dans le flux), puis `rec.onstop` (passé async) envoie vidéo + WAV stéréo à `/api/export/finalize` → le serveur mux la piste son exacte (-c:v copy). Échec réseau → rien décompté, message clair
  - mode hybride (WebCodecs) : déjà audio serveur
  - Chrome/desktop : inchangé (audio client validé)
- ✅ **Anti-cache** : `Studio.js` charge l'iframe avec `/studio.html?v=${Date.now()}` → chaque chargement récupère la DERNIÈRE version du studio (Safari gardait potentiellement une vieille version en cache après les déploiements !)
- ✅ Non-régression Chromium testée : export téléchargé, piste audio opus présente et audible
- 📢 Signal de vérification pour l'user : sur iPhone, pendant l'export, l'étape « Ajout du son (serveur)… » DOIT apparaître — si absente, l'app tourne encore sur l'ancien build (fermer l'onglet Safari et rouvrir)
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (12 juillet 2026) — 🔴 INCIDENT « projet perdu » : protections anti-perte de données complètes
- Incident user prod : export « diaporama » (vignettes fixes) → rechargement bloqué 3/34 → autosave a ÉCRASÉ le projet avec un état vide → projet perdu
- Chaîne causale : fetchMedia sans timeout (blocage), restore partiel non détecté, autosave aveugle, export silencieux en mode secours vignettes
- ✅ **Sauvegardes versionnées serveur** : `project_backups` (15 versions/projet, index (project_id, created_at)) — snapshot AVANT chaque save qui PERD des clips (`reason: perte-de-clips`) + snapshot auto max 1×/10 min. Endpoints : GET `/api/projects/{id}/backups`, POST `/api/projects/{id}/backups/{bid}/restore` (backup 'avant-restauration' d'abord)
- ✅ **Verrou anti-écrasement** : `restoreIncomplete` → si ≥1 clip échoue au chargement, `persistRemote()` REFUSE de sauvegarder (#saveState « ⚠ Sauvegarde désactivée ») + toast explicite
- ✅ **fetchMedia robuste** : 3 tentatives + AbortController anti-stall (30 s sans octets → abort → retry) — plus de chargement gelé à 3/34
- ✅ **Bouton « ☁ Récupérer mes vidéos déjà envoyées »** (banque, `data-testid=recover-media-button`) : GET `/api/media/mine` (limite 1000) → ré-ajoute toutes les vidéos GridFS absentes de la banque, avec barre de progression, puis réactive la sauvegarde
- ✅ **Bouton « 🕘 Versions »** (barre du studio, `data-testid=backups-button`) : popup listant les versions (date, nb vidéos, nb plans) avec Restaurer (confirm + reload)
- ✅ **Garde anti-diaporama** : `ensureClipsReady()` avant TOUT export — chaque vidéo utilisée par un plan doit être décodable (readyState≥2 + videoWidth>0, réveil load() + attente 6 s) sinon export REFUSÉ avec message clair + console.warn
- ✅ Testé (iteration_9) : backend 7/7 pytest (backup perte-de-clips, restore, throttle, scoping, 401/404), frontend : popup versions OK, verrou OK (0 POST), récupération 15 vidéos OK, lecture OK. Export bloqué en headless par la garde = comportement CORRECT (codecs H.264 absents du headless)
- 📢 Pour le projet perdu de l'user : après redéploiement → ouvrir le projet → « ☁ Récupérer mes vidéos » restaure la banque (les plans/le montage restent à refaire, les backups n'existaient pas encore à ce moment). Les vidéos GridFS n'ont PAS été supprimées (GC uniquement à la suppression de projet)
- ⚠️ REDÉPLOIEMENT nécessaire

## Implémenté (13 juillet 2026) — 🚀 PHASE 2 : MOTEUR VIDÉO DÉFINITIF 100 % WEBCODECS (façon LYRC)
- Demande user : « MOTEUR VIDÉO DÉFINITIF — ON PASSE AU WEBCODECS, MODE UNIQUE » (bascule totale choisie, pas de toggle). Prototype de référence /tmp/moteur-lyrc-test.html suivi À L'IDENTIQUE (ordre de décodage mp4box jamais trié, description avcC/hvcC W3C, pas d'optimizeForLatency, backpressure 10 frames, frame.close() systématique)
- ✅ `<script src="/vendor/mp4box.all.min.js">` chargé (vendorisé) + filtre du bruit BoxParser des mp4 iPhone
- ✅ `parseClipWC(clip, blob)` : démuxage mp4box → `clip.wc={samples[] (ordre de décodage), config (codec+description), durationS}` + `VideoDecoder.isConfigSupported` ; fin d'extraction par stabilisation du compte d'échantillons (fiable sur gros fichiers) ; flags `_wcReady/_wcFail/_wcParse`
- ✅ `class SegPlayer` : lecteur de segment à double tampon (seek → keyframe scan → décodage, fill() borné à 10 frames / queue 14, frameAt(t) draine jusqu'à la cible)
- ✅ LECTURE : double lecteur wcA/wcB — pendant qu'un plan joue, wcB pré-décode le plan suivant → à la coupure, permutation (latence ~0). `syncLivePlan`/`wcActivate`/`wcWarmUp` ; `play()` et `startLoop()` attendent la 1re frame décodée (max 2,5 s) avant de lancer le son ; reboucle si un plan dépasse la durée du clip
- ✅ SCRUB à l'arrêt : décodeur dédié `wcScrub` re-calé à la demande + redraws différés (wcScrubRedraw) → plus aucun seek `<video>`
- ✅ EXPORT : `wcExportSeek` décode séquentiellement, critère d'exactitude « la frame suivante dépasserait la cible » → validé 12/12 timestamps EXACTS (frame-accurate). exportOffline branché dessus (plus de seekPlanFrame quand WC actif)
- ✅ VIGNETTES : `wcMakeThumbs` génère les thumbs via WebCodecs (un seul décodeur, seek par sous-plan) — plus de <video> pour les thumbs quand le codec est décodable
- ✅ Gating strict : `clipsBlocking()` inclut l'état de parse WC → lecture impossible tant que les clips ne sont pas démuxés/bufferisés
- ✅ REPLI automatique : navigateur sans WebCodecs/MP4Box → ancien moteur <video> intact (warmUpPlansTag/activatePlan/poolEl conservés) ; clip au codec indécodable (ex. HEVC avant optimisation Mux) → _wcFail → métadonnées+vignettes via <video> + fallback vignettes à la lecture, ré-essai automatique après swap Mux (swapClipMedia re-parse)
- ✅ Série de vidéos : drawVariantFrame + serieWaitClips + ensureClipsReady branchés WC
- ✅ data-testid song-card/data-song-id sur les cartes home (testabilité) ; log [wc] dédupliqué par clip
- ✅ TESTÉ (iteration_10, 100 % backend 5/5 + 100 % frontend) : parse VP9 240 samples, thumbs 4/4, lecture wcPtr avance + canvas non noir + arrêt auto, loop, scrub, sauvegarde+reload projet, série 3 versions, 0 erreur JS
- ⚠️ Chromium headless du pod SANS codecs H.264 → clips H.264 = _wcFail en test (ATTENDU, pas un bug) ; clips VP9 de test : /wc_test_a.mp4 et /wc_test_b.mp4 (servis statiquement, à conserver pour les retests)
- 📢 VALIDATION USER REQUISE sur PC Chrome (environnement réel) : lecture fluide, coupures nettes, export rapide
- ⚠️ REDÉPLOIEMENT nécessaire

## Backlog priorisé (mise à jour 13 juillet 2026)
- P1 (après validation user du moteur) : UpChunk pour uploads reprenables
- P1 : Emails Resend automatiques en cas d'échec d'export
- P2 : Nettoyage systématique des fichiers orphelins GridFS

## Implémenté (13 juillet 2026) — MODE UNIQUE : suppression totale de l'ancien moteur <video>
- Décision user : PAS de repli <video> (c'était l'ancien moteur bugué) → un seul moteur WebCodecs, point.
- ✅ SUPPRIMÉ (~200 lignes) : exportRealtime (MediaRecorder), makePoolVideo, poolEl, assignPlanPlayers/planAssign, activatePlan, prepareNext, ensureActive, warmUpPlansTag, seekPlanFrame, livePtr/liveEl, toutes les branches WC_ON — 0 résidu (grep vérifié)
- ✅ Navigateur incompatible : `engineSupported()` (VideoDecoder+VideoEncoder+VideoFrame+EncodedVideoChunk+Mp4Muxer+MP4Box) vérifié via `engineGuard()` à l'ouverture de l'ÉDITEUR (openEditor) et de genSerie → écran bloquant « BeatCut a besoin d'un navigateur récent — Chrome, Edge, Safari ou Firefox à jour » avec 4 liens de téléchargement + bouton retour (data-testid=unsupported-browser-screen)
- ✅ CHAQUE affichage de l'écran est loggué : POST /api/telemetry/unsupported-browser (ua + user_id si session) → collection `browser_unsupported_logs` ; mesure admin : GET /api/admin/telemetry/unsupported-browser {total, last_30d, samples}
- ✅ Export : offlineSupported()===false → message clair « mets ton navigateur à jour », rien décompté (plus de repli temps réel) ; échec exportOffline → message d'erreur propre, rien décompté
- ✅ CONSERVÉ (pas un moteur) : repli <video> UNIQUEMENT pour métadonnées/vignettes d'un clip au codec indécodable (HEVC iPhone) en attendant le swap Mux → re-parse WebCodecs automatique
- 🐛 BONUS corrigé : duplication de clips au chargement (course hashchange + route() → loadRemoteMorceau lancé en double → addClip dupliqués PERSISTÉS). Verrou `m._loading` dans loadRemoteMorceau. Reproduit avec 3× route() → 5 clips uniques ✓. Fixture « Morceau Série Test » réparée (clipRefs restaurés depuis la backup 13:21, dédupliqués)
- ✅ Testé : syntaxe node OK, lecture WebCodecs re-validée après suppression (wcPtr avance, canvas non noir), thumbs 4/4, écran incompatible affiché/loggué/fermé (simulation VideoEncoder=undefined), endpoints télémétrie 200
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (13 juillet 2026) — Aperçus des clips manquants après import + Mélanger
- Bug user : « quand on importe la vidéo l'aperçu des clips marche pas et Mélanger n'utilise que les 3 seuls clips qui ont un aperçu »
- Causes racines identifiées et corrigées :
  1. SATURATION DÉCODEURS : import multiple → un wcMakeThumbs (décodeur WebCodecs) par clip EN PARALLÈLE → au-delà de ~3-4, les décodeurs matériels refusent → vignettes vides. FIX : file d'attente globale `_thumbQ` (une génération à la fois) + retry avec un décodeur neuf si `p.err` + jeton `_thumbGen` (annule la passe obsolète après swap Mux) + renderClips() après chaque vignette (feedback progressif)
  2. SEEKS JAMAIS CRÉÉS : original HEVC illisible par <video> (pas de loadedmetadata) → seeks=[] → après le swap Mux, makeThumbs tournait sur 0 seeks → clip définitivement sans aperçu. FIX : startClipUpload régénère les seeks depuis clip.wc.durationS après le re-parse du swap + autoAssign()
  3. p.seek=undefined si seeks vide dans shufflePlans/autoAssign/removeClip → FIX : garde `(c.seeks&&c.seeks.length)? … : 0`
- ✅ Testé (pod, clips VP9) : import ×6 simultané → 6 clips avec 4/4 vignettes ; Mélanger → 20 plans, 0 seek invalide ; simulation swap Mux sans seeks → 4 seeks + 4 vignettes régénérés
- 📢 VALIDATION USER REQUISE avec ses vrais fichiers (iPhone/HEVC) sur son navigateur
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (13 juillet 2026) — Vignettes noires sur clips LONGS (photo utilisateur : 55ASKY ~2 min)
- Symptôme : sur un clip long, les vignettes des sous-plans tardifs (54s, 71s, 106s, 123s…) restaient noires
- Cause racine : budget FIXE de 1,5 s par vignette. Sur un GOP long (keyframe toutes les 5-10 s, typique des clips musicaux), décoder depuis la keyframe précédente jusqu'à la cible prend plusieurs secondes (surtout mobile) → abandon → vignette noire
- FIX : `wcAwaitFrame(p, t, slack)` — attente basée sur la PROGRESSION du décodeur (on continue tant que p.si avance ou que des frames arrivent ; abandon seulement après 2,5 s sans progrès, garde-fou absolu 12 s). Appliqué aux vignettes ET à `wcExportSeek` (l'export sur GOP long aurait eu le même trou)
- ✅ Testé (pod) : clip VP9 140 s, keyframe toutes les 10 s → 8/8 vignettes générées (jusqu'à 125 s) ; export frame-accurate sur un plan à 119,7 s (timestamps exacts au pas de 24 fps)
- Fichier de test long supprimé de public/ (les petits wc_test_a/b.mp4 restent pour les retests)
- 📢 VALIDATION USER REQUISE avec ses vrais clips longs
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (13 juillet 2026) — Export MUET depuis téléphone (PRODUCTION, iPhone Safari + Chrome iOS)
- Diagnostic confirmé avec le user : la vidéo se télécharge mais est MUETTE. Cause : WebKit iOS expose AudioEncoder et `isConfigSupported('mp4a.40.2')` répond supported → mode export 'full' (AAC client) → mais l'encodage AAC réel produit une piste inutilisable (pas de description codec / chunks invalides) → mp4 muet livré
- FIX en 3 couches (mp4 muet désormais impossible) :
  1. `_aacReallyWorks()` : AVANT l'export, encodage RÉEL de ~0,3 s de silence → exige un chunk AVEC decoderConfig.description ; sinon mode 'hybrid' (son assemblé serveur)
  2. Pendant l'export 'full' : le 1er chunk AAC sans description → rejeté (aencErr), rien de muxé
  3. Filet final : si `aencErr` ou `audioChunks===0` après flush → bascule automatique vers /api/export/finalize (serveur ajoute la piste, -c:v copy, 2-3 s) au lieu de livrer un mp4 muet. Erreur audio ≠ erreur fatale (seule la vidéo peut faire échouer l'export)
- ✅ Vérifié : /api/export/finalize testé en preview (HTTP 200, sortie avec Stream audio aac stéréo 192k) ; _aacReallyWorks/offlineSupported s'exécutent proprement (pod sans AAC → hybrid/false honnête) ; syntaxe OK
- ⚠️ Le fix est en PREVIEW : le user doit REDÉPLOYER pour corriger la production (beat-cut.com)
- ⚠️ Point de vigilance prod : le chemin hybrid POST ~50 Mo (vidéo+wav) vers /api/export/finalize — si l'ingress prod limite la taille du body, l'utilisateur verrait « assemblage du son impossible » → contacter le support Emergent dans ce cas

## Corrigé (13 juillet 2026) — Export muet iPhone : SOLUTION DÉFINITIVE (son serveur forcé sur mobile)
- Le fix précédent (test AAC réel) ne suffisait pas : WebKit iOS peut réussir le test ET produire une piste AAC muette à l'usage
- FIX DÉFINITIF : `MOBILE_UA` (iPhone/iPad/Android + iPad desktop-UA via maxTouchPoints) → mode 'hybrid' FORCÉ : sur mobile le son est TOUJOURS assemblé par le serveur (ffmpeg, AAC parfait), plus jamais l'encodeur AAC du navigateur
- Diagnostics ajoutés :
  - Toast final indique le mode : « son : assemblé par le serveur » / « son : direct » → l'utilisateur peut nous rapporter le chemin réellement pris
  - Détection de source silencieuse : peak de l'extrait mesuré avant export → toast d'alerte si ~0 (morceau mal rechargé)
  - Erreur d'assemblage serveur avec code HTTP (ex. « HTTP 413 » = limite d'upload ingress prod → support Emergent)
  - Télémétrie : POST /api/telemetry/export {mode, server_audio, audio_chunks, aenc_err, src_peak, size, ua} → collection export_logs + GET /api/admin/telemetry/exports (admin)
- ✅ Testé preview : endpoints télémétrie 200 (insert + lecture admin), studio charge sans erreur, MOBILE_UA=false sur desktop, /api/export/finalize déjà validé (piste AAC présente)
- ⚠️ NÉCESSITE REDÉPLOIEMENT pour effet sur beat-cut.com. Si encore muet après ça : lire le toast final + /api/admin/telemetry/exports pour trancher (source silencieuse vs upload bloqué)

## Corrigé (13 juillet 2026) — Export bloqué par « Optimisation en arrière-plan » + optimisation trop longue
- Bug user : impossible d'exporter tant que le badge optimisation est là, et il dure longtemps
- FIX 1 (front) : `clipsExportBlocking()` remplace `clipsOptimizing()` pour l'export — ne bloque QUE si un clip UTILISÉ dans les plans n'est pas décodable localement (`!_wcReady` et (`_optimizing` ou `!_wcFail`)). Un upload/optimisation en arrière-plan ne bloque PLUS JAMAIS l'export (le moteur WebCodecs lit l'original local). Même logique assouplie pour genSerie. `clipsOptimizing()` supprimée (orpheline)
- FIX 2 (back) : `_probe_video()` (ffmpeg -i) avant Mux — si la vidéo est DÉJÀ H.264 ≤1080p à ≤12 Mbps → transcodage SAUTÉ (metadata.transcode_skipped), optimisation ~1 s au lieu de 30-90 s. media_status expose `skipped` ; le front ne re-télécharge pas le fichier dans ce cas (pas de swap inutile)
- ✅ Testé : upload mp4 H.264 propre → « Transcodage sauté … @ 2.1 Mbps » en ~1 s, status {transcoded:true, skipped:true} ; gate export validé sur les 5 cas (ready+optimizing→libre, fail+optimizing→bloqué, fail seul→libre avec message ensureClipsReady, tous prêts→libre, clip non utilisé en optimisation→libre)
- ⚠️ REDÉPLOIEMENT nécessaire

## Vérifié + instrumenté (13 juillet 2026) — Export iPhone muet : chaîne son PROUVÉE SAINE en preview
- Test de bout en bout exécuté avec le vrai code : buffer du morceau → extractWavStereoBlob (peak source 0.676) → POST /api/export/finalize (200) → mp4 final analysé par ffmpeg volumedetect : piste AAC stéréo avec SIGNAL RÉEL (mean −19,3 dB, max −6,2 dB). Le code preview NE PEUT PAS produire un mp4 muet via le chemin serveur ; ffmpeg force -map 1:a:0 (le WAV), et le muxer client ne déclare pas de piste audio en mode hybrid
- Hypothèse principale restante : la PROD n'exécute pas la dernière version (déploiement pas refait après le fix « son serveur forcé mobile », ou cache iOS)
- Instrumentation ajoutée pour trancher : `BC_BUILD='v13.07-son-serveur'` loggé en console + AFFICHÉ dans le toast de fin d'export + envoyé dans la télémétrie export (champ build). GET /api/admin/telemetry/exports montre build/mode/server_audio/src_peak/aenc_err par export
- PROTOCOLE UTILISATEUR : redéployer → exporter depuis l'iPhone → lire le toast final : il DOIT contenir « v13.07-son-serveur » et « son : assemblé par le serveur ». Sinon = ancienne version en prod. Puis consulter https://beat-cut.com/api/admin/telemetry/exports (connecté admin) et rapporter le JSON

## Terminé (17 juillet 2026) — Système de codes promo AFFILIÉS (Stripe, remise à vie)
- Backend : POST/GET/DELETE /api/admin/affiliate (coupon Stripe duration=forever, % ou € fixe, plans configurables, commission % pour suivi admin), GET /api/affiliate/check/{code} (public), checkout accepte promo_code → discount Stripe auto
- Suivi admin : abonnés actifs par code, revenu mensuel généré, commission calculée (AffiliateAdmin.js dans le panneau admin)
- Application côté user : saisie du code sur /dashboard OU lien /?promo=CODE (mémorisé en localStorage bc_affiliate) → bandeau prix barrés
- Testé : iteration_11.json 100% backend (11/11 pytest) + 100% frontend ; self-test post-fixes (dup 400, plan non couvert 400 explicite, checkout couvert 200, delete 200)
- Fixes finaux (17/07) : index unique affiliate_codes.code + compensation stripe.Coupon.delete si doublon (anti double-clic) ; 400 explicite « Ce code affilié ne couvre pas ce plan » / « Code affilié invalide ou expiré » au checkout ; bandeau visible aussi pour les abonnés BASIC (upgrade PRO avec remise visible, choix user), caché pour PRO/VIP ; doublon champ email dans payment_transactions supprimé
- ⚠️ REDÉPLOIEMENT nécessaire pour effet sur beat-cut.com

## Backlog
- P1 : UpChunk pour uploads vidéo reprenables
- P1 : Resend — email auto sur échec d'export
- P2 : Nettoyage systématique des fichiers GridFS orphelins

## Terminé (17 juillet 2026) — UX code promo affilié : remise SUR les prix (plus de bandeau)
- Bandeau "🎁 Code XXX actif" au-dessus des prix SUPPRIMÉ (montrait le code à tout le monde via les liens ?promo=CODE)
- Remise affichée directement SUR les boutons de prix : prix barré + prix remisé + petit badge 🎁 CODE en haut à gauche (data-testid price-basic/monthly/yearly, promo-badge-{plan}) — pour les gratuits (3 plans) ET le bouton upgrade PRO des BASIC
- Texte carte code promo : « Tu as déniché un code promo ? Rentre-le ici. »
- ✅ Testé screenshots : sans code = prix normaux sans badge ; avec code = 6,99→6,29 / 12,99→11,69 / 99→89,10 + badges sur les 3 boutons ; upgrade BASIC avec prix barré
- Compte test créé : qa_free_ui@test.local / Testing1234! (user FREE, non nettoyé)
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (17 juillet 2026) — Code promo affiché sans avoir été saisi (BYRON collé)
- Cause : un lien ?promo=CODE stockait le code en localStorage POUR TOUJOURS → remise affichée indéfiniment même sans saisie
- FIX : lien ?promo=CODE → sessionStorage bc_affiliate_link (session en cours seulement) ; saisie manuelle → localStorage bc_affiliate_manual (persistant, prioritaire) ; ancienne clé localStorage bc_affiliate purgée à chaque chargement (App.js) — corrige aussi les users déjà touchés en prod après redéploiement
- ✅ Vérifié par bug_testing_agent (iteration_12) : 100% — sans code = pas de badge ; legacy purgé ; lien = session only ; manuel persiste au reload ; checkout régression OK
- ⚠️ REDÉPLOIEMENT nécessaire pour beat-cut.com

## Terminé (22 juillet 2026) — Studio : édition avancée des sous-titres + lecture au curseur + fix Série
- FIX BUG « Série de vidéos » : « Préparer les vidéos » chargeait dans le vide — fetchRemoteMorceau affichait #loadOverlay mais le flow série n'appelait jamais hideLoad() → overlay à vie. genSerie appelle maintenant hideLoad() + try/catch/finally (aiBar.done() + bouton réactivé garantis)
- Sous-titres timeline : multi-sélection (clic / Maj-clic plage / Ctrl-clic toggle), déplacement GROUPÉ par drag, copier (⧉ ou Ctrl+C), coller au curseur de lecture (📋 ou Ctrl+V, écarts relatifs conservés), supprimer (🗑 ou touche Suppr) — barre #wordSelBar dans la tl-bar, état selWords (Set) + wordClip
- Suppression des mots IA : bouton 🗑 + touche Suppr sur sélection (avant : seulement Delete sur bloc focus, obscur)
- Lecture au curseur : togglePlay (bouton ▶ / Espace) démarre depuis startOff (position cliquée sur la timeline) ; pause mémorise la position ; clamp → redémarre au début si curseur hors extrait
- ✅ Testé iteration_13 : 100% frontend (bug série reproduit puis confirmé corrigé, 7 features + 4 régressions PASS)
- ⚠️ REDÉPLOIEMENT nécessaire pour beat-cut.com

## Terminé (22 juillet 2026) — Corrections de la revue de code
- Credentials de test sortis du code : backend/.env (TEST_DEMO_*, TEST_ADMIN_*, TEST_VIP_*) + /app/backend/tests/creds.py (chargement dotenv, fail fast) — 7 fichiers de test migrés, 0 credential en dur restant
- 52 comparaisons `is True/False` → `== True/False` dans les tests ; import `time` inutilisé supprimé ; pyflakes clean sur server.py + tests
- exec() du rapport = FAUX POSITIF : asyncio.create_subprocess_exec (ffmpeg, args fixes, sans shell) — aucune modification
- Refactoring PUR de server.py : create_checkout → _plan_pricing + _apply_affiliate_discount ; _stripe_revenue_stats → _sub_monthly_cents/_stripe_mrr_cents/_stripe_charge_totals ; _mux_transcode → _mux_create_upload/_mux_wait_asset_id/_mux_wait_mp4
- Test obsolète corrigé : test_affiliate_iter11 attend maintenant 400 pour un plan non couvert (11/11 pass)
- ✅ Testé iteration_14 : 43/44 puis 44/44 après correction du test obsolète — checkout 3 plans + affilié, stats admin Stripe, endpoints Mux, greps sécurité clean
- Refactors différés (P2, non bloquants) : promo_apply, sub_info, stripe_webhook, save_project, media_import_url — code fonctionnel, à découper si retouché

## Terminé (27 juillet 2026) — Lot V3 (cahier des charges) + DA globale + pages légales
- studio.html remplacé par studio-v3-complet.html (fichier fondateur, déployé tel quel — contient FR/EN, plans/vidéo, sans coupes, telemetry webview) ; landing statique beatcut-landing.html servie en / (iframe Landing.js + patch target=_top des liens internes)
- Backend : POST /api/telemetry/webview (public) + GET /api/admin/telemetry/webview (admin) → collection webview_logs
- DA « Nuit de studio » appliquée à toutes les pages React via index.css : palette #0B0E13/#12161D/#232B36, Archivo Black uppercase (.font-display), dégradé rouge REC sur .bg-primary, boutons/inputs arrondis, radius 14px
- Pages légales (React, DA appliquée, routes + liens footer) : /cgv, /confidentialite, /mentions-legales, /contact — éditeur « société FAUT » (pas de SIRET), contact jules.beatcut@gmail.com
- Seed demo corrigé : abonnement BASIC re-signé +30 j à chaque démarrage (ne peut plus expirer) ; bouton Contact illisible corrigé (!text-white !no-underline)
- ✅ Testé iteration_15 (backend 7/8→8/8 après fix seed, frontend 95%→100% après fix bouton) — studio v3 régression complète OK (série, multi-sélection mots, FR/EN persistant)
- Reste du cahier des charges (prochaines étapes) : §2-A télémétrie aperçus (preview_logs), §2-B KPIs admin previews, §2-C décision serveur de prévisualisation ; §3 plan annuel = DÉJÀ EN PROD
- ⚠️ REDÉPLOIEMENT nécessaire

## Terminé (2 août 2026) — Contact landing + logo BEATCUT + nouveaux presets sous-titres
- FIX : lien 'Contact' du footer landing → /contact (avant : mailto:contact@beat-cut.com) — navigue la fenêtre principale (target=_top)
- Logo : 'BEATCUT' collé et en majuscules partout (landing header+footer, studio) — cause de l'espace : gap flex entre nœuds texte, corrigé par <span>BEAT<b>CUT</b></span>
- 8 nouveaux presets sous-titres (studio) : Affiche (Archivo Black + DÉGRADÉ rouge sur texte), Comics (Bangers), Marqueur (Permanent Marker), Manuscrit (Caveat), Pixel (Silkscreen+scanlines), Usé (Rubik Distressed), Étroit (Archivo Narrow), Terminal (JetBrains Mono) → 20 presets, aussi dans Série
- 2 nouvelles animations mots : Zoom + Secousse (boutons #fAnim, i18n EN OK) ; nouveau prop style.grad (createLinearGradient dans drawLyricBlock, reset {grad:false} à chaque changement de preset)
- ✅ Testé iteration_16 : 15/15 assertions PASS (contact e2e, logos, 20 presets, anims, dégradé, série, i18n)
- ⚠️ REDÉPLOIEMENT nécessaire

## Terminé (7 août 2026) — §2-A Télémétrie des aperçus (cahier des charges)
- Studio : objet TEL (session_id, batching 25 events / flush 20s / sendBeacon à la fermeture) + 4 sondes : preview_stall (même frame >500ms en lecture, dédupliqué par épisode, avec plan/clip/codec/wcReady/queue/buffered), frame_miss (repli vignette en lecture, throttle 1/s), decoder_error (SegPlayer._telErr : callback error + catch decode + codec non supporté), clip_not_ready (play() pendant optimisation Mux, 2 emplacements)
- Backend : POST /api/telemetry/preview (public, whitelist des champs, cap 100 events/batch) → collection preview_logs ; GET /api/admin/telemetry/preview?days=N (admin) : % sessions gelées, par cause/navigateur (_browser_family)/taille projet (buckets)/codec + samples
- Admin : panneau « Télémétrie aperçus (§2) » dans /admin (PreviewTelemetryAdmin.js, sélecteur 3/7/30 jours)
- ✅ Testé iteration_17 : backend 8/8, frontend 11/11
- PROCHAINES ÉTAPES CdC : §2-B classifier après 3-5 jours de données réelles en prod (rapport % par cause) → §2-C corriger UNIQUEMENT la cause dominante. Validation : -80% de preview_stall sur la cause traitée
- ⚠️ REDÉPLOIEMENT nécessaire (les données ne se collectent qu'en prod)

## Terminé (27 juillet 2026) — Bug CSS anim, série améliorée, ZIP unique, import par lien
- FIX CSS : boutons animation (#fAnim, 6 boutons) débordaient avec scrollbar → .seg{flex-wrap:wrap}
- Série : versions toutes DIFFÉRENTES (pool mélangé de combos clip+seek, évitement doublons à la même position entre versions + variété intra-version) ; aperçus fluides (warmUpPlans avec les plans de la version AVANT le son, bouton ⏳→⏸)
- Téléchargement série : UN SEUL .zip (buildZip maison, mode STORE + CRC32, sans lib externe) contenant toutes les vidéos ; quota décompté N fois au téléchargement (_dlRegister/dlPendingCount avec info.count) ; repli une-par-une si erreur zip
- Import clip par LIEN : champ 🔗 dans la colonne clips (i18n FR/EN) → POST /api/media/import-link (yt-dlp nightly + node 24 via nodejs-wheel-binaries + ffmpeg imageio_ffmpeg, tâche de fond, statuts queued/downloading/storing/done, garde SSRF, cap 78 Mo/1080p, isolation par user) → GET status → API.fetchMedia → addClip
- ⚠ LIMITATION CONNUE : YouTube bloque souvent les IP datacenter (403) → message d'erreur explicite ; TikTok/Vimeo/.mp4 directs fonctionnent (Vimeo + mp4 validés E2E)
- ✅ Testé iteration_18 : backend 8/8, frontend 100% (CSS, UI lien, série variantes/aperçu, buildZip, régressions)
- ⚠️ REDÉPLOIEMENT nécessaire

## Corrigé (28 juillet 2026) — Export série bloqué après vidéo 1 + barre unique + retrait import lien
- CAUSE : exportVideo(nameSuffix, sink) n'avait PAS transmis sink à exportOffline → ReferenceError 'sink is not defined' à la fin de la vidéo 1 → catch → boucle interrompue. FIX : exportOffline(nameSuffix, mode='full', sink, batch)
- Barre de progression UNIQUE pour le lot série : 'Export vidéo 2/3 — 45 %' avec % global continu (bLbl/bPct), pas de fermeture entre vidéos (cleanup: aiBar.done() seulement si !batch), aiBar.done() une fois après la création du zip
- Import par lien RETIRÉ à la demande de l'utilisateur (YouTube bloque les IP datacenter) : champ 🔗 + importClipLink + API.importLink supprimés du studio. Endpoints backend /api/media/import-link conservés (fonctionnels, inutilisés)
- ✅ Testé iteration_19 : 100% — espion exportOffline : la vidéo 2 EST exportée après la 1 (chaîne complète), zip unique '2 vidéos (.zip)', barre continue, champ lien absent, régressions OK
- ⚠️ REDÉPLOIEMENT nécessaire

## Terminé (28 juillet 2026) — Refonte UX MOBILE (façon CapCut)
- Éditeur studio ≤700px : écran verrouillé sans scroll (header 50px avec titre + Exporter TOUJOURS visible, aperçu 1fr, transport 52px, timeline 148px) ; body.mob-edit posé par route(), header studio + wrapper React masqués sur mobile
- Barre d'outils basse #mobBar (5 onglets 🎬 Clips · 🎵 Son · 📝 Paroles · 🎨 Style · ⚙️ Plus, data-testid mob-tab-*) → bottom sheets coulissants (.col / #extractZone / #mobMore, un seul ouvert, re-tap ou tap dehors = fermer, i18n FR/EN)
- Plus (#mobMore) : Annuler, Versions, FR/EN, Accueil, Mon compte (window.top → /dashboard)
- Cibles tactiles ≥44px (boutons), transport/tl-bar une ligne en scroll horizontal (plus de chevauchement des formats 9:16/1:1/…), timeline compacte
- Série mobile : 1 carte/ligne (≤300px centrée), styles 2 colonnes ; pages accueil/morceaux : grille 2 colonnes
- Dashboard : fix overflow horizontal (min-w-0 sur cartes Parrainage/Code promo)
- ✅ Testé iteration_20 : 100% (mobile 390×844 + régression desktop 1280px)
- ⚠️ REDÉPLOIEMENT nécessaire

## Implémenté (28 juillet 2026) — 🏷️ REFONTE TARIFAIRE COMPLÈTE (brief_tarifs.md) — testé iteration_21
### Nouvelle grille (§1)
- Plans : **Essentiel 9,99 €/mois** (15 exports/mois, pas de séries) · **Pro 19,99 €/mois** (essai 7 j, illimité+séries) · **Pro Annuel 149 €/an** · **Studio 499 €/an** (watermark perso, 3 sessions, démo par mailto)
- Backend : `_plan_pricing` étendu (prix inline Stripe), `sub_info` → tiers free/essentiel/basic/pro/studio + `trial/trial_end`, quotas export réécrits (free=402 paywall, essai=cap 15, essentiel=15/mois reset date anniversaire via `_essentiel_period_start`, basic legacy=10/mois inchangé), `PLAN_PRICES/PLAN_LABELS/LEGACY_PLAN_EQUIV` (codes affiliés legacy couvrent les nouveaux plans équivalents)
### Essai 7 jours (§2)
- Checkout pro_monthly → `trial_period_days:7` (sauf trial_used/fingerprint déjà connu) ; `_guard_trial_fingerprint` post-checkout : carte déjà utilisée pour un essai → abonnement annulé (payment_status `trial_refused`), sinon empreinte stockée (`trial_fingerprints`) + `trial_used`
- Webhook `customer.subscription.trial_will_end` → email rappel Resend (trial_reminder_email_html) ; webhook-setup met à jour les enabled_events des endpoints existants (⚠️ PROD : re-cliquer « Activer le webhook Stripe » dans /admin après déploiement)
- `POST /api/payments/activate-now` (fin d'essai anticipée trial_end=now) ; annulation PENDANT l'essai = cancel Stripe immédiat, 0 débit, email
- Parcours sans carte : free = 1 morceau (quota projets), **5 clips max** (403 à l'upload vidéo), export → modale paywall studio (`paywall-modal`, 4 offres) ; `return_path` dans checkout → retour /studio?project=ID&session_id → `checkPaidReturn()` (projet intact)
### Sessions uniques (§3)
- `sids` sur le user (JWT claim sid + session_token Google), 1 session (3 studio, ∞ admin/VIP) — `_check_sid` → 401 « Ton compte a été connecté sur un autre appareil. » Tolérance : sessions d'avant le mécanisme valides jusqu'au prochain login. CGV mises à jour (compte individuel)
### Grandfathering (§4) : anciens plans basic/monthly/yearly intacts (tests 200 OK), plus proposés nulle part
### Landing + app (§5-6)
- landing.html : pastille essai, 4 cartes (Essentiel / Pro badge « Le plus choisi » / Pro Annuel doré −38 % / Studio mailto démo), réassurance, FAQ essai, **0 occurrence « gratuit »/« sans carte »** (vérifié grep) ; Dashboard : grille 4 plans, badge SANS ABONNEMENT/ESSAI PRO/ESSENTIEL/STUDIO, quota bar 15 ou 10, bandeau « ESSAI PRO — Jx/7 », annulation essai dédiée, **upload watermark PNG Studio** (POST/GET/DELETE /api/studio/watermark, incrusté bas-droit 12 %/85 % via studioWM dans drawPreview)
- Studio : compteur 🔒 pour free, messages 19,99 €, séries bloquées essentiel/free, trial banner + modale trial_cap avec activation anticipée
### Onboarding (§6bis)
- Overlay studio 5 écrans + écran hype « ES-TU PRÊT… » + écran final dépôt du son (crée le morceau + ouvre l'éditeur, preset par genre : rap_drill→impact, plugg_hyperpop→neon, afro_shatta→comics, pop_chanson→karaoke, electro_club→glitch) ; « Passer » enregistre skipped_at ; flag `onboarding_done` (nouveaux comptes register+Google = false, legacy = true) ; POST /api/onboarding + /api/telemetry/onboarding (collection onboarding_logs) ; réponses visibles dans GET /api/admin/users
### Emails Resend RÉELS : clé re_CWTg… en .env, domaine beat-cut.com vérifié, sender no-reply@beat-cut.com
### Tests : iteration_21 = backend 20/20 + régression 28/28 (après fix LEGACY_PLAN_EQUIV) + frontend 7/7 (après fix wording landing) ; pytest test_basic_plan adapté au paywall 402 ; nouveau fichier tests/test_iter21_pricing_refonte.py
### ⚠️ ACTIONS PROD après REDÉPLOIEMENT
1. Re-cliquer « ⚡ Activer le webhook Stripe » dans /admin (ajoute trial_will_end aux événements)
2. Vérifier RESEND_API_KEY + SENDER_EMAIL repris dans les env prod
3. Les sessions existantes des clients restent valides jusqu'à leur prochain login (tolérance sids vide)

## Backlog (mise à jour 28 juillet 2026)
- P1 : §2-B analyse télémétrie aperçus en prod → §2-C fix cause dominante des freezes
- P1 : UpChunk uploads reprenables ; email Resend auto sur échec d'export
- P2 : Studio multi-profils produit (lot ultérieur explicitement exclu du brief) ; nettoyage GridFS orphelins ; DELETE /api/media/{id}

## Implémenté (29 juillet 2026) — correctifs post-refonte
- Mail Studio corrigé partout : mailto **jules.beatcut@gmail.com** (paywall studio, Dashboard, landing) — contact@beat-cut.com supprimé
- Admin : nouvelles cartes « En essai gratuit (7 j) » (Stripe trialing, fallback DB trial_users) et « Convertis depuis l'essai » (trial_used + payant réel actif) ; « Abonnés actifs (payants réels) » = Stripe status=active uniquement (les trialing n'y figurent PAS) ; compteurs plans mis à jour (yearly inclut pro_yearly/studio, basic inclut essentiel)
- 🐛 FIX suppression code promo : le seed startup recréait les codes par défaut (BIENVENUE50/LAUNCH30/BEATCUTSTART) après chaque redémarrage → les suppressions sont maintenant mémorisées dans db.config `deleted_promo_codes` et jamais recréées. Testé : delete + restart backend → le code ne revient plus
- Confirmé au user : les anciens abonnements Stripe ne bougent pas (grandfathering, aucun prix modifié côté Stripe)

## Implémenté (29 juillet 2026 — suite) — Admin : répartition plans + suivi annulations
- Taux de conversion essai : case « Convertis depuis l'essai » affiche X (Y %) — trial_started (trial_used=True) / trial_converted / trial_conversion_rate dans /api/admin/stats
- Répartition par plan (payants réels) : 4 cases nouveaux plans (Essentiel 9,99 / Pro 19,99 / Pro annuel 149 / Studio 499) + 3 cases anciens (Basic 6,99 / Pro 12,99 / Pro annuel 99) — champ `plans` dans stats ; MRR estimé fallback recalculé avec les 7 plans
- **GET /api/admin/cancellations** : liste des annulations (email, plan, annulé le, accès jusqu'au, statut « Accès encore actif »/« Terminé ») triée par date desc — nouvelle section « Suivi des annulations » dans /admin (testée avec un user factice puis nettoyé)

## Implémenté (29 juillet 2026 — suite 2) — Formulaire d'annulation + offre de rétention −50 %
- Le clic « Se désabonner »/« Annuler mon essai » ouvre maintenant un formulaire 2 étapes (Dialog) : ① raison (6 choix : too_expensive, not_enough_use, missing_features, technical_issues, promo_done, other + commentaire facultatif 500 car.) → ② offre « −50 % sur ta prochaine facture » (si abonnement Stripe réel, jamais utilisée : flag retention_offer_used) ou simple confirmation
- Backend : POST /api/subscription/cancel-feedback (collection cancel_feedback {user_id, email, plan, trial, reason, comment, retained, at}), POST /api/subscription/retention-accept (coupon Stripe 50% duration=once caché dans db.config retention_coupon, appliqué via Subscription.modify discounts) ; cancel réel → _mark_feedback_lost (retained=False)
- Admin : section « Pourquoi ils annulent » — barres % par raison, cartes « Restés grâce à l'offre −50 % (X %) » / « Partis quand même », derniers commentaires ; données dans stats.cancel_feedback
- Testé : formulaire UI (screenshot), 400 raison invalide, agrégations %, section admin. Offre −50 % non testable de bout en bout sans vrai abonnement Stripe (LIVE) — code conforme API Stripe 14 (discounts=[{coupon}])
- 29/07 : offre rétention −50 % restreinte aux plans MENSUELS (RETENTION_PLANS) — refus 400 sur pro_yearly/yearly/studio, testé

## Implémenté (29 juillet 2026 — suite 3) — Refonte UX MOBILE du studio (≤700px), testée
- **Accueil** : barre d'onglets fixe en bas `#homeTabs` (Accueil · Morceaux · Série · Compte→/dashboard), nav header masquée, header épuré (logo + quota pill + avatar 36px), hero resserré avec CTA pleine largeur, onglet actif suivi via hashchange (updateHomeTabs)
- **Éditeur** : bouton ← retour `#editBack` (mobile only), transport sans débordement : `#fmtSeg` remplacé par bouton ratio cyclique `#fmtCycle` (cycleFmt() → 9:16→1:1→4:5→16:9, délègue aux boutons cachés), BPM chip compact
- **Timeline** : pistes plus hautes (paroles 32px, plans 104px), plans arrondis 88px borde 2px, tl-bar chips pill 36px scrollables (hint/kbd masqués), fix libellé toggleSnap («Beat : ON/OFF»)
- **Bottom sheet « Ce plan »** `#planSheet` au tap d'un plan (mobile, desktop garde planPop) : 🔄 Remplacer le clip (grille horizontale des clips → verrouille), 🎲 Autre plan (seek suivant du même clip ou clip aléatoire), ✂️ Découper en 2 (cut au milieu), 🗑 Supprimer (fusion avec le voisin via suppression de la coupe), 🔒 verrou. Fonctions psReplace/psOther/psSplit/psDelete/psLockToggle (~l.4050). mobSheet() ferme le planSheet
- i18n EN ajouté pour les nouveaux libellés. Desktop vérifié intact (fmtSeg visible, nouveaux éléments display:none)
- Testé par navigation scriptée mobile 390px : split 20→21, delete 21→20, autre plan, undo, retour accueil, tabs OK

## Implémenté (29 juillet 2026 — suite 4) — Fix landing MOBILE (rapport screenshot prod)
- Cause racine du rendu cassé : la nav débordait horizontalement (liens + CTA wrappés) → scroll-x + font boosting iOS. Fixes : `html,body{overflow-x:hidden}` + `-webkit-text-size-adjust:100%`, nav ≤600px = logo + Connexion + CTA compact (liens Comment/Tarifs masqués), h1 clamp(34px,10.5vw,42px), CTA hero pleine largeur, kicker sans trait
- Doublon CTA : le sticky bas n'apparaît plus que lorsque le CTA hero sort de l'écran (IntersectionObserver)
- Vérifié : overflow-x = 0, rendu propre 390px. ⚠️ Le user voit la PROD (beat-cut.com) : redéploiement nécessaire pour voir le fix. NOTE : dernier deploy a échoué (Cloud Build docker-push, probablement transitoire) — retenter.
- 29/07 : annulations d'ESSAI marquées « Essai Pro (avant débit) » dans /admin → Suivi des annulations (flag subscription.was_trial posé au cancel trial, exposé par /api/admin/cancellations, badge bleu dans Admin.js). Testé + nettoyé.

## Implémenté (29 juillet 2026 — suite 5) — Fix tl-bar PC + emphase sous-titres + onglet Effets embelli
- 🐛 tl-bar desktop : boutons qui wrappaient sur 2 lignes → nowrap + scroll-x + hint ellipsis (`.tl-bar` l.208), vérifié 29px/1 ligne
- ⭐ **Mot mis en avant toutes les 2 mesures** : nouveaux props style `emph/emphScale/emphColor/emphFont` ; logique isEmph dans drawLyricBlock (per=480/bpm, premier mot de chaque fenêtre de 2 mesures) ; mode word = taille×couleur×police, modes line/spread = couleur+police seulement ; drawWordAt accepte param emph ; s'applique preview ET exports (même pipeline)
- UI carte `#emphCard` dans Style→Effets : toggle + slider taille (1.1–2) + 6 swatches couleur ronds (= même couleur / rouge / jaune / vert / bleu / violet) + select police ; bord accent + glow quand actif ; sync via syncStyleUI, sauvegardé avec « Mon style » et le projet
- Onglet Effets embelli : checkboxes → cartes toggle (bord accent quand coché, :has), effets vidéo en grille 2 colonnes `.fx-grid`
- Testé par screenshots desktop : tl-bar propre, carte emphase, grille effets. i18n EN ajouté
- 29/07 (correctif emphase) : la mise en avant cible désormais les mots dits sur le DERNIER temps du cycle (fenêtre [cyc−beatDur, cyc), grille calée sur beats[0], tolérance 0.02s) + réglage Fréquence 1/2/4 mesures (style.emphEvery, seg #xEmphEvery). Logique validée par test unitaire node + UI vérifiée en screenshot.


## Implémenté (30 juin 2026 — fork)
- ✅ **Bouton "Passer en illimité maintenant"** (Dashboard) pour les utilisateurs en essai gratuit : dialog de confirmation (débit immédiat 19,99 €) → `POST /api/payments/activate-now` (Stripe `trial_end="now"`). Le studio avait déjà ce bouton au cap d'essai ; le Dashboard l'affiche désormais en permanence pendant l'essai.

## Backlog
- P0 : Erreur Cloudflare intermittente au login ("response that Cloudflare could not parse") — NON DÉMARRÉ
- P1 : Nettoyage systématique des fichiers orphelins GridFS
- Suivi : lags/freeze lecture vidéo (télémétrie en prod, en attente de données)

- ✅ **Tutoriel mobile studio** (30 juin 2026) : coach-marks 7 étapes au premier montage sur mobile (≤700px) — bienvenue, Son, Clips, Paroles, Style, timeline, Export. Spotlight sur les vrais éléments UI, points de progression, bouton Passer, FR/EN (map i18n), télémétrie (`mobtuto_start/step/done/skipped` via /api/telemetry/onboarding), flag `localStorage bc_mobtuto_done`.

## Implémenté (30 juin 2026 — suite)
- ✅ **Tutoriel desktop** : même tour guidé 7 étapes adapté PC (>700px) — cibles #stageWrap, #clipDrop, #tabP, #tabS, #trPlans, #exportBtn, carte 400px positionnée près de la cible. Même clé localStorage bc_mobtuto_done (1 affichage par appareil).
- ✅ **Fenêtre « Maintenant, tes vidéos 🎬 »** après le flux onboarding : questionnaire → dépôt du son → tuto → modale onb-video-modal avec « ＋ Ajouter mes vidéos » (ouvre le sélecteur de clips), « 🔎 Banque de vidéos gratuites » (ouvre le panneau Clips + focus recherche Pexels), « Plus tard ». FR/EN, télémétrie onb_video_*. Fix : setTimeout(0) pour éviter que le clic de la modale referme le tiroir mobile (handler clic extérieur).
- ⚠️ Rappel : ces nouveautés (tuto + fenêtre vidéos + bouton activation essai) ne sont PAS encore en production — redéploiement nécessaire.

## Implémenté (30 juin 2026 — stats onboarding)
- ✅ **GET /api/admin/onboarding-stats** : funnel tuto (démarrés/terminés/passés + taux via onboarding_logs mobtuto_*), questionnaire terminé/passé, distribution des réponses par question (users.onboarding.*).
- ✅ **Admin > section « Onboarding & tutoriel »** (admin-onboarding-section) : 4 stats tuto + barres de répartition des 5 questions (labels FR jolis).
- ✅ **3 écrans de stats motivantes** insérés dans le questionnaire d'onboarding (après persona, release_timing, current_method) : « un artiste poste 2×/semaine… », « 80 % des streams dans les 2 premières semaines », « montage à la main ~45 min vs BeatCut <2 min ». Compteur de questions inchangé (x/5), télémétrie onboarding_info_N.

## Revue de code appliquée (30 juin 2026)
- FAUX POSITIF : les 4 « exec() » signalés = asyncio.create_subprocess_exec (listes d'arguments, pas de shell) — sûrs, aucun changement.
- FAUX POSITIF : « variables indéfinies » — pyflakes clean sur server.py.
- ✅ Secrets retirés des tests : test_iter21_pricing_refonte.py et test_import_link_iter18.py importent désormais creds.py (backend/.env : TEST_FREE_EMAIL/TEST_FREE_PASSWORD ajoutés). Les mots de passe jetables de comptes TEST_ créés à la volée (backend_test.py) sont des fixtures, pas des secrets.
- ✅ Refactor stripe_webhook : handlers par type d'événement (_wh_checkout_completed, _wh_trial_will_end, _wh_subscription_sync) + dispatch _WEBHOOK_HANDLERS.
- ✅ Refactor create_checkout : _build_checkout_params + _maybe_add_trial extraits.
- ✅ Refactor _claim_and_activate : guard clauses / early returns (nesting 6 → 2).
- Non fait (choix délibéré, risque > bénéfice sur du code paiement LIVE fonctionnel) : redesign sub_info/admin_preview_report, state machine média, classe PromoValidator.
- Régression : 48/48 tests pytest PASS (iter21 + basic_plan + affiliate_iter11).

## Fix cuts BPM élevé (30 juin 2026)
- ✅ buildPlans() (studio.html ~2035) : suppression du `step = bpm>=140 ? 2 : 1` — les coupes auto se font désormais sur CHAQUE temps quel que soit le BPM. Vérifié sur la fixture Recette 150BPM : 76 cuts à 0,4 s (avant : 38 cuts à 0,8 s).
- Note : les morceaux déjà sauvegardés conservent leurs anciennes coupes tant que l'extrait/BPM n'est pas modifié (les cuts sont persistés) ; toute régénération applique la nouvelle règle.

## Fix mise en avant des mots (30 juin 2026)
- ✅ isEmph() (studio.html ~3305) : la grille des mesures est désormais ancrée sur le DÉBUT DE L'EXTRAIT (mesure 1, temps 1 perçu = beat le plus proche de ext.start) au lieu de beats[0] du morceau entier. Fenêtre inchangée : mots dont le start ∈ [4e temps, 1 de la mesure d'après), toutes les 1/2/4 mesures (style.emphEvery).
- Libellé UI + EN mis à jour : « du 4e temps au 1 de la mesure d'après ».
- Vérifié sur fixture Recette 150BPM : 'cent' (3,25 beats) et 'bpm' (3,5) emphatisés, 'recette'/'cinquante' non.

## Fix export Safari macOS (2 août 2026)
- ✅ Vidéos muettes sur Mac/Safari : ajout SAFARI_UA (WebKit desktop, hors Chrome/Edge/Firefox) → offlineSupported() force le mode 'hybrid' : le son est TOUJOURS assemblé par le serveur (/api/export/finalize, -c:v copy), jamais via l'AudioEncoder WebKit (pistes AAC muettes constatées).
- ✅ Téléchargements qui échouent sur Safari : dlGo() — l'ancre n'est plus retirée de façon synchrone (Safari annule le téléchargement) → retrait différé 2 s, rel=noopener, fallback window.open.
- Testé : régression UA (Safari mac/iOS → true ; Chrome/Edge/Firefox → false), endpoint /api/export/finalize validé E2E (mp4 sortant = h264 + aac).
- ⚠️ À REDÉPLOYER pour beat-cut.com.

## Mise en avant par CLIC manuel (2 août 2026) — FAIT
- ✅ isEmph() = w.emph (flag par mot, persisté dans M.words) — le mode automatique beat a été retiré.
- ✅ Panneau Style → Effets → « Mots mis en avant » : sélecteur de mots cliquables (#xEmphWords, chips .ew, data-testid emph-word-N) + réglages complets avec héritage « = » : Taille (1–2,5), Couleur (swatches), Police (liste complète = celle du texte), Épaisseur, Casse, Contour, Fond derrière le mot, Lueur, Ombre, Inclinaison (segs xEmph*, valeurs '' = comme le texte).
- ✅ drawWordAt() applique les overrides (font/weight/case/outline/box/glow/shadow/rot par mot, rotation locale save/restore).
- ✅ FIX PERSISTANCE IMPORTANT : openEditor fait maintenant M.style=style (même référence) — avant, les réglages de style modifiés après chargement d'un projet AVEC préset n'étaient jamais sauvegardés (style et M.style étaient 2 objets distincts).
- Testé E2E : clic mots, réglages, rendu canvas sans erreur, persistance après reload (mots + réglages + UI restaurée).
- ⚠️ À REDÉPLOYER pour beat-cut.com.

## Fix vignettes manquantes Safari (3 août 2026)
- Symptôme (photos utilisateur, Mac Safari) : quelques vignettes OK puis toutes noires/absentes (grille + plan et timeline).
- Causes traitées dans studio.html :
  1) makeThumbsTag/makeThumbAtTag capturaient sur 'seeked' — sur WebKit la frame n'est présentée qu'à la vsync suivante → noir. Désormais capture via requestVideoFrameCallback (fallback rAF+40ms).
  2) Chaîne séquentielle sans timeout : un seek silencieux bloquait TOUTES les vignettes suivantes → timeout 5-6 s par vignette + guard « même currentTime » (seeked ne tire pas) + gestion error.
  3) _wcMakeThumbsNow : après la passe WebCodecs, les index encore vides sont complétés via <video> (filet WebKit quand le décodeur cale).
  4) Rendu progressif (renderClips à chaque vignette) aussi sur le chemin <video>.
- Vérif : syntaxe JS OK (node --check), page sans erreur console. ⚠️ Environnement headless sans codecs H.264 → test décodage réel impossible ici : l'utilisateur doit REDÉPLOYER puis vérifier sur son Mac.

## Fix Cloudflare 520 login (3 août 2026)
- Cause identifiée : course keep-alive — uvicorn ferme les connexions inactives à 5 s (défaut) alors que Cloudflare/l'ingress les réutilisent plus longtemps → requête sur connexion en fermeture → réponse tronquée « could not parse » intermittente (souvent au login après inactivité).
- ✅ server.py : _bump_uvicorn_keepalive() patch les protocoles h11/httptools d'uvicorn → timeout_keep_alive 120 s (indépendant de la ligne de commande, s'applique aussi en prod au redéploiement). Vérifié par socket brut : connexion maintenue >15 s (avant : fermée à ~5 s).
- ✅ frontend/src/lib/api.js : retry automatique unique (800 ms) sur erreurs de transport (pas de réponse, 502/504/520-527) pour les GET et les routes /auth/* — filet si un proxy produit encore un raté.
- ⚠️ À REDÉPLOYER pour effet sur beat-cut.com.

## Nettoyage GridFS automatique (6 août 2026)
- ✅ FIX CRITIQUE PRÉALABLE : _project_media_ids ne lisait que le format v1 (clips[].mediaId) alors que les projets v2 stockent audioMediaId + clipRefs[].mediaId → corrigé (les 2 formats). Sans ça, le nettoyage aurait supprimé les fichiers des utilisateurs ET la suppression de projet ne purgait rien.
- ✅ _cleanup_orphan_media() : référence = tous les projets + project_backups + watermarks users ; marge 24 h sur uploadDate ; rapport stocké dans db.config (media_cleanup_last).
- ✅ _media_cleanup_loop() : au démarrage (+120 s) puis toutes les 24 h. Premier passage réel : 39 orphelins / 211,6 Mo libérés en preview.
- ✅ Endpoints POST/GET /api/admin/media/cleanup + section Admin « Stockage (GridFS) » (admin-media-cleanup-button / -result).
- Testé : 6 fixtures (orphelin vieux → supprimé ; orphelin récent, réf clipRefs, réf audioMediaId, réf backup, réf watermark → tous préservés) + UI admin OK.

## Codes promo x nouveaux abonnements (6 août 2026)
- ✅ /api/promo/apply réécrit : le code donne un ACCÈS PRO TEMPORAIRE via user.promo_pro_until (+N jours, cumulable), SANS toucher subscription (un Essentiel garde son plan, sa date et ses 9,99 €). Avant : le code étendait current_period_end du plan existant (un Essentiel gagnait des jours d'Essentiel, pas de Pro).
- ✅ sub_info() : si promo_pro_until > now → tier forcé à 'pro' (sauf studio, rank free<basic/essentiel<pro<studio), champs promo/promo_until exposés ; user 100% free → status/plan 'promo', fin = promo_until.
- ✅ Quota/stockage suivent le tier → illimité pendant la promo, retour auto au plan payé à l'expiration.
- ✅ Dashboard : bannière 🎁 (promo-access-banner) « accès PRO offert jusqu'au X — ton abonnement continue normalement » ; bouton Se désabonner masqué pour les purs promo (status 'promo').
- Testé curl+UI : essentiel→pro (plan/période intacts, quota illimité), free→pro 30 j, réutilisation refusée (400).

## Admin fiche client + CGV obligatoires (11 août 2026)
- ✅ GET /api/admin/customer?email= : fiche complète (compte, sub_info, ids + état Stripe live, promo, 50 derniers paiements). POST /api/admin/customer/cancel : annulation IMMÉDIATE (stripe.Subscription.cancel + statut local expired + fin=now + promo purgée) — plus aucun prélèvement. Faux/anciens sub Stripe tolérés.
- ✅ Admin UI section « Rechercher un client » (admin-customer-*) : recherche email, fiche, table paiements, bouton 🛑 annuler avec confirmation 2 temps.
- ✅ Inscription : case CGV OBLIGATOIRE (front + backend 400 sans cgv_accepted), cgv_accepted_at horodaté en DB, liens CGV/Confidentialité (nouvel onglet), mention d'acceptation sous le bouton Google.
- ✅ CGV renforcées : §2 acceptation par case à cocher horodatée, §9 données personnelles (RGPD), §10 modification des CGV (préavis 30 j), §11 médiation de la consommation (L611-1 + plateforme ODR), §12 droit applicable & juridiction.
- ✅ 13 payloads register des suites pytest mis à jour (cgv_accepted). Régression : 37/37 PASS.

## Briques serveur pour l'app mobile (12 août 2026)
- ✅ /app/backend/mobile_render.py : analyze_bpm (flux d'énergie + autocorr + prior 125 BPM anti-octave, phase optimisée), build_ass (sous-titres mode mot + emph), build_render_cmd (segments trim/concat 1080x1920 + ass + aac).
- ✅ POST /api/audio/analyze (60 Mo max) — testé : wav 120 BPM → bpm 120.0, 40 beats.
- ✅ POST /api/export/render (job asynchrone, db.render_jobs, gate tier free=403, dur cap 90 s, 120 segments max, timeout 10 min, sortie GridFS + export_logs) + GET /api/export/render/{job_id}. Testé E2E : job done en 5 s, MP4 h264 1080x1920 + AAC 8 s, sous-titres OK, mot emph rouge/gros OK, alternance clips sur beats OK.
- ✅ /app/memory/MOBILE_APP_BRIEF.md mis à jour (endpoints marqués disponibles) — à donner au Mobile Agent dans un NOUVEAU projet.
- requirements.txt regénéré (pip freeze).

## Essai 7j → 3j + rappel J-1 fiable (13 août 2026)
- ✅ TRIAL_DAYS = 3 ; tous les textes « 7 jours » mis à jour (server.py, Dashboard.js, CGV.js, AuthPage, Navbar, studio.html paywall + bannière J/3, landing.html x10).
- ✅ _trial_reminder_loop (horaire, +180 s au boot) : essais se terminant sous 24 h → email « Ton essai Pro se termine demain » + flag trial_reminder_sent. Enregistrée au startup.
- ✅ _wh_trial_will_end neutralisé sauf si fin < 36 h (Stripe envoie l'événement 3 j avant la fin = au DÉBUT d'un essai de 3 j → aurait envoyé le rappel trop tôt).
- ✅ Email J-1 : titre « Ton essai se termine demain », rappel du prix 19,99 €, bouton « Gérer ou annuler » → /dashboard. Aperçu partagé à l'utilisateur.
- Régression : 37/37 pytest PASS. ⚠️ À REDÉPLOYER.
- Note : les essais Stripe déjà en cours (créés à 7 j) gardent leur durée d'origine ; seuls les nouveaux checkouts partent sur 3 j.

## Email J-1 bouton activation + stats cohortes essais (13 août 2026)
- ✅ _email_html supporte 2 boutons (cta2). Email J-1 : bouton principal « ⚡ Passer en illimité maintenant » → /dashboard?activate=1, bouton secondaire « Gérer ou annuler ».
- ✅ Dashboard : ?activate=1 ouvre automatiquement la modal d'activation immédiate si l'utilisateur est en essai.
- ✅ _guard_trial_fingerprint stocke trial_days + trial_started_at au démarrage de chaque essai. /api/admin/stats expose trial_cohorts {d7,d3} (started/converted/rate) — les essais historiques sans trial_days comptent en 7 j. Admin : Stat « Conversion essais 7 j vs 3 j ».
- Testé : aperçu email 2 boutons OK, modal auto sur ?activate=1 OK (demo simulé trialing puis restauré), trial_cohorts d7 1/0 correct.

## Fluidité de l'aperçu éditeur (17 août 2026) — bug récurrent (5e signalement)
- Causes identifiées : (1) ctx.filter saturation appliqué à CHAQUE frame (rendu logiciel très lent) ; (2) imageSmoothingQuality 'high' par frame ; (3) décodeur WebCodecs pompé uniquement dans la rAF → famine quand le thread principal charge.
- ✅ Correctifs studio.html : filtre saturation déplacé en CSS GPU sur #preview pendant la lecture (ctx.filter conservé à l'arrêt + export → rendu final identique) ; smoothing 'medium' en lecture ; pompe wcPump (setInterval 20 ms) démarrée dans play(), stoppée dans stopAll() ; pause propre sur visibilitychange (onglet masqué).
- ✅ Télémétrie low_fps : fenêtre 5 s, TEL.push si <20 fps (fps, sat, nb plans, largeur codec, buffered) → données prod pour la suite.
- Testé par testing_agent (iteration_23.json) : 100 % PASS (wcPump start/stop, bascule CSS filter lecture/pause, rAF vivante, scrub, loop, modale export, 0 erreur JS). ⚠️ Validation FPS réelle impossible en headless (pas de codecs H.264) → la télémétrie low_fps tranchera en production. À REDÉPLOYER.

## Proxy preview serveur + préchargement 2 coupes (14 août 2026)
- ✅ Backend : POST /api/media/proxy/{media_id} (auth + ownership, idempotent, cache via metadata.proxy_of). Génération FFmpeg H.264 Main ≤720p sans audio, keyframes 0,5 s, faststart (_ffmpeg_proxy/_make_proxy/_auto_proxy).
- ✅ Proxy AUTOMATIQUE à l'upload (choix utilisateur) : _transcode_media déclenche _auto_proxy à chaque fin (sauté/succès/échec). Vidéo déjà H.264 ≤720p → proxy_skipped (renvoie son propre id).
- ✅ Proxys exclus du quota (_storage_used) et de /media/mine ; nettoyage orphelins déjà compatible (metadata.proxy_of).
- ✅ Studio v13.08-proxy-preview : ensureClipProxy (polling 3 s ×100, télécharge + parseWC → clip.wcProxy ; devient la source principale si clip indécodable, régénère seeks/vignettes). La preview préfère le proxy (wcPrev), l'EXPORT garde la pleine résolution (clip.wc).
- ✅ Triple décodeur wcA/wcB/wcC : 2 coupes pré-décodées à l'avance (rotation à l'activation, warmUpPlans + wcPump inclus) — coupes rapides sans famine du décodeur.
- ✅ Bug corrigé : startPexelsImport appelé mais JAMAIS défini (ReferenceError à l'ajout d'un clip Pexels) → défini via API.importMedia en arrière-plan.
- ✅ Nettoyage : ancienne route dupliquée /media/proxy (sans auth, code mort ligne 3420) supprimée.
- Testé : testing_agent iteration_24.json — backend 7/7 PASS, frontend 100 % PASS (0 erreur JS). ⚠️ À REDÉPLOYER pour effet en production.

## RCA Cloudflare « could not parse » + optimisation mémoire (15 août 2026)
- 🔎 RCA (agent déployeur, prod) : pod backend OOMKilled (exit 137, 13 restarts) — tier_0 Starter = 512Mi. Chaque kill coupe les requêtes en vol → erreur Cloudflare intermittente au login. PAS un bug de code login ni de keep-alive.
- ⚠️ ACTION UTILISATEUR REQUISE : monter le tier dans Deployment Panel → Resources (min Grow, idéal Scale vu FFmpeg).
- ✅ Code — empreinte mémoire divisée : pipeline transcodage 100 % flux disque (_grid_to_file, _ffmpeg_transcode/_ffmpeg_proxy sur chemins, _mux_transcode upload/download streaming avec Content-Length), TRANSCODE_SEM 6→1, ffmpeg -threads 2.
- ✅ /api/media/upload et /api/media/import-url : spool disque par morceaux de 1 Mo (_store_media_file remplace _store_media bytes), hash sha256 en flux.
- ✅ /api/export/finalize (Safari, jusqu'à 600 Mo) : copie UploadFile→disque par morceaux + réponse en flux (plus jamais l'export entier en RAM).
- ✅ _run_render (mobile) : téléchargement GridFS en flux.
- ✅ Monkey-patch keep-alive uvicorn retiré (faux-piste confirmée par la RCA).
- ✅ Suite pytest réparée (pollution inter-tests pré-existante) : 159/159 PASS. Corrigés : promo REGRESSDAY laissait un bonus Pro sur démo ; test_projects_lot4 supprimait les projets fixture (fixture preserve ajoutée) ; logins multiples vs mode session unique (logout test → user jetable, cookies transférés dans TestRegression) ; assertion promo format obsolète. Projets démo restaurés depuis les backups.
- 📌 Note séparée : quota Mux atteint (plan gratuit 10 assets) → tous les transcodages passent par le repli FFmpeg local (plus de CPU/RAM sur le pod). À traiter : nettoyer les assets Mux ou upgrader le plan Mux.
- ⚠️ À REDÉPLOYER après montée de tier.

## Refonte visuelle V3 — Phases 1-3 (19 août 2026)
- Brief fondateur « monument obsidienne » : noir #000, cramoisi #fc1c46, Space Grotesk, zéro ombre/rayon (sauf pilules), 1 pilule cramoisie/écran, thème clair/sombre partagé (localStorage bc_theme).
- ✅ Landing : /landing.html remplacée par v3 (essai « 3 jours » partout — choix utilisateur vs brief 7 j ; ancienne = landing-v2-backup.html). Curseur custom, onde héro 52 barres, halos héro+plan Pro, FAQ, tarifs 9,99/19,99/149/499.
- ✅ Studio rhabillé (PAS réécrit) via /v3-skin.css : jetons V2 remappés → V3, pilules, segments .on fond blanc, inputs soulignés, ranges v3, timeline, mobile bar. #exportBtn = seule pilule cramoisie éditeur. Fonts Space Grotesk ajoutée.
- ✅ Pages Accueil/Mes morceaux v3 (renderCards réécrit : onde seedée + coupes cramoisies, badge état, tags style, date relative, suppression, i18n) + bouton thème header (themeBtn) + bouton 🔒 Verrouiller dans la tl-bar (lockAtPlayhead sur plan sous la tête de lecture).
- Testé testing_agent iteration_25.json : 100 % PASS, 0 exception JS (landing dark/light, thème partagé, cartes réelles, outils timeline, segments, export modal). toggleLang re-render les pages listes.
- ⏳ RESTE (Phase 4, « tout le site ») : AuthPage.js, Dashboard.js (Mon compte), pages légales, Admin.js, page Série aux jetons v3. ⚠️ À REDÉPLOYER après Phase 4.

## Refonte V3 — Phase 4 + vignettes réelles (19 août 2026)
- ✅ Tout le site React aux jetons v3 : index.css réécrit (tokens shadcn HSL dark + [data-theme=light], Space Grotesk, pilules, zéro ombre/rayon), index.html lit bc_theme (thème partagé landing↔studio↔app React), Toaster sonner noir, rec-dot = carré cramoisi.
- ✅ Pages passées : AuthPage, Dashboard (badge basic bordé, 1 seule pilule cramoisie = Passer en Pro, annuel sans jaune, promo-submit fantôme), Navbar (studio ghost), Footer, Admin (violets #8f9bff éliminés), légal, Projects, Reset/Forgot.
- ✅ Vignettes réelles : renderCards affiche m.thumb (<img>, capturée du canvas à l'autosave — mécanique backend déjà en place) avec repli onde seedée.
- Testé testing_agent iteration_26.json : 100 % PASS, 0 erreur JS (auth, dashboard, cgv, admin, vignettes réelles avant/après autosave, thème partagé, régressions). 2 mineurs corrigés post-test (promo-submit, violets admin).
- ⚠️ À REDÉPLOYER. Point 11 recette (export réel Chrome + Safari iPhone) à valider par l'utilisateur.

## Refonte V3 — Fidélité maquette + purge émojis + emails (19 août 2026, suite)
- ✅ Double barre supprimée : Studio.js = iframe plein écran (plus de barre React) ; en mode éditeur le header global du studio disparaît (body.editing) — edit-top unique façon maquette (←, logo, titre inline, Enregistré, thème, Annuler, Versions, Série, halo Exporter).
- ✅ PURGE TOTALE des émojis sur tout le site (studio.html, landing, toutes pages React, i18n.js, server.py/emails) — script regex uniforme, dico i18n cohérent. Tolérés : ← → ▶ ❚❚ ✕ ✓ ★ ☀ ☾. Barre mobile = texte pur.
- ✅ Onglets colonne droite soulignés cramoisi (maquette), segments restent pilules fond blanc. Play ▶/❚❚.
- ✅ Emails Resend : gabarit central _email_html refait en DA v3 (noir #000, bordure #171717, pilule cramoisie #fc1c46, capitales, carré rouge logo, zéro émoji) — vérifié visuellement.
- Testé testing_agent iteration_27.json : 100 % PASS desktop + mobile, aucun bug.
- ⚠️ À REDÉPLOYER.

## Curseur V3 point + anneau (20 août 2026)
- ✅ Curseur custom maquette (point 6px + anneau 26px, mix-blend difference, hover .hit 44px, clic .down 18px, lerp .16) sur TOUTES les pages : app React (index.js + index.css), studio.html (script DOMContentLoaded + v3-skin.css), landing (déjà présent).
- ✅ Desktop uniquement (@media hover+pointer:fine), délégation mouseover (éléments dynamiques du studio couverts).
- ✅ Anti-double-curseur : les routes iframe (/ landing et /studio) posent body.no-cur → curseur parent masqué, celui de l'iframe fait foi ; retiré au unmount (dashboard etc. le récupèrent).
- Testé par vérifications Playwright ciblées : .cur/.cur-ring présents, cursor:none, .hit au survol des boutons, no-cur correct sur les 3 contextes.

## UX Studio V3 : menu latéral mobile, tuto v3, overlay, sélecteurs (20 août 2026)
- ✅ Mobile : barres du bas (#homeTabs nav + #mobBar édition) transformées en DRAWER LATÉRAL droit ouvert par hamburger (#homeBurger dans header, #editBurger dans edit-top) + scrim + bouton ✕ ; les panneaux/pages récupèrent le bas d'écran (padding 0, sheets bottom:0). Aperçu centré, zéro scroll (vérifié).
- ✅ Tuto mobile réécrit : 4 étapes (Bienvenue → Le menu ☰ → Timeline → Exporter), carte DA v3 (noir, capitales, pilule cramoisie), spot v3 (#mtSpot exception box-shadow). Tuto desktop = mêmes styles, cibles inchangées.
- ✅ Overlay chargement assets : plein écran noir, texte capitales, barre 2px cramoisie (fini gradient violet + cadre).
- ✅ Sélecteurs .seg/.subtabs : pilules internes dans conteneur arrondi 18px, wrap propre, aucun mot coupé (photo bugs 1 & 4 réglés). Play/pause centré (grid). Curseur réduit 20/32px partout (photo 2). Mode clair : .preset fond sombre forcé → polices de démo visibles (photo 5).
- ✅ Edit-top mobile : title width fix (débordement réglé), export compact, burger visible.
- ✅ Landing : eyebrow « Montage vidéo pour la musique » supprimé.
- Testé testing_agent iteration_28.json : 27/31 (échecs = faux positifs sélecteurs + garde export normale en headless « vidéo pas prête », vérifiée manuellement). ⚠️ À REDÉPLOYER.

## Contraste sombre, langue, fixes mode clair, bouton admin tuto (20 août 2026, soir)
- ✅ Mode sombre plus contrasté (même DA) : --ash #d9d9d9, --graphite #7a7a7a, --hair #1d1d1f, --hair-2 #3a3a3e (v3-skin.css + index.css HSL + landing.html).
- ✅ Langue : React i18n default = langue navigateur (navigator.language) — toggle FR/EN déjà présent dans la Navbar (toutes pages app) + studio (langBtn, déjà navigateur par défaut). Textes i18n.js « 7 jours » corrigés → 3 jours. Landing reste FR (statique).
- ✅ Photo 1 : #fsBtn (Plein écran) passé en pilule v3 (fond void, bordure hair-2). Photo 2 : halo radial du .canvas-wrap supprimé → fond plat var(--lift). Photo 3 : input[type=range] max-width calc(100%-12px) → le pouce ne sort plus de sa case (vérifié par mesure DOM).
- ✅ Bouton ADMIN « Revoir tuto » (header studio, role==='admin' uniquement, data-testid=admin-replay-tuto-btn) : relance le questionnaire d'entrée (showOnboarding) + efface bc_mobtuto_done → tutoriels remontrés. Vérifié en screenshot avec le compte admin.
- Auto-testé par screenshots + mesures DOM (petits changements CSS/JS ciblés).
- 20 août soir : pouce des input[type=range] réduit 13px→9px (grossissait trop dans la fenêtre, mode clair) — vérifié screenshot.
- 21 août : cache-buster ajouté sur v3-skin.css (?v=13.09) + BC_BUILD v13.09-ux-v3 — l'utilisateur voyait l'ancien CSS en cache (slider). Alignement rail/dropzone vérifié au pixel (221=221).

## Aperçus animés des effets + scrollbars invisibles (21 août 2026)
- ✅ Onglet Effets : les 10 cases à cocher deviennent des cartes .fx-card avec aperçu animé du logo BEATCUT■ (keyframes CSS par effet : flash, zoom punch, secousse, glitch 2 couches, VHS scanlines, grain, saturé, glow flou, caméra instable, fisheye). Clic carte = coche l'input (ids xv* inchangés, handlers intacts, vérifié). Bordure cramoisie quand actif (:has(input:checked)). prefers-reduced-motion respecté.
- ✅ Barres de scroll masquées dans les colonnes du studio (.col scrollbar-width:none + webkit display:none, overflow-x hidden) — le défilement reste actif.
- Cache-buster v3-skin.css → ?v=13.10.

## Curseur avec marges + interface 90 % (21 août 2026, suite)
- ✅ input[type=range] : margin-right 16px — le rail/pouce s'arrête 14px avant le bord de la case (mesuré : dropRight 199 / rangeRight 184).
- ✅ Interface à 90 % : html{zoom:.9} dans v3-skin.css (studio) et index.css (app React), avec html:has(body.no-cur){zoom:1} pour éviter le double zoom sur les routes iframe (/ landing reste 100 %, /studio parent 1 × studio .9). Vérifié : login/dashboard 0.9, parents iframe 1.
- Cache-buster → ?v=13.11.
- 21 août (fix) : html{zoom:.9} RETIRÉ du studio (décalait le curseur custom et cassait canvas/timeline — incompatible coordonnées souris). App React : 90 % obtenu via html{font-size:14.4px} (rem Tailwind, aucun impact coordonnées), pages iframe exclues (:has(body.no-cur)). Alignement curseur vérifié au pixel (600,400=600,400). Cache → ?v=13.12. NE PLUS JAMAIS utiliser zoom CSS dans le studio.

## Bande noire + aperçus mots + landing EN (21 août 2026)
- ✅ Bande noire bas d'écran : body.editing masque le header (56px) mais #pageEdit gardait calc(100vh-56px) → ajout v3-skin : body.editing #pageEdit{height:100dvh} + grid-rows 58px 1fr 185px (desktop ≥901px seulement, mobile intact). Vérifié : peBottom == innerHeight.
- ✅ Aperçus animés « Apparition des mots » : #fAnim devient .wa-grid avec 6 cartes animées (wa-card-none/pop/fade/slide/zoom/shake), handlers existants intacts ($$('#fAnim button')).
- ✅ Landing bilingue : dict EN + applyLang (TreeWalker) dans landing.html, détection navigator.language, bouton FR/EN (bc_lang partagé studio).

## Batch pricing 7j + suppression compte + purge IA + onboarding v3 (21 août 2026)
- ✅ Essai 3 → 7 jours PARTOUT : backend TRIAL_DAYS=7 (Stripe LIVE trial_period_days), emails, paywall, CGV (J+7), Dashboard (badge J/7), AuthPage, i18n, landing, bannière studio.
- ✅ DELETE /api/auth/account : annule Stripe, efface GridFS (metadata.user_id), projects, backups, sessions, user. UI : carte « Supprimer mon compte » (Dashboard) + modal confirmation tapée SUPPRIMER. Testé (iteration_29 : 100% PASS).
- ✅ Landing : CTA héro « Commence maintenant », section #securite (fichiers chiffrés, zéro IA générative, suppression compte), phrases sous CTA héro et lead tarifs SUPPRIMÉES (demande user).
- ✅ Purge mentions IA (studio aiBar « Analyse · », tuto, hints, Dashboard) — seule mention restante : section Sécurité landing.
- ✅ Footer unifié PARTOUT (logo Beatcut■ + CGV · Confidentialité · Mentions légales · contact@beat-cut.com, RIEN d'autre) : landing, React Footer.js, studio #studioFoot (masqué en édition).
- ✅ Navbar React v3 cohérente : MES MORCEAUX → /studio, MON COMPTE → /dashboard, pill FR/EN, logout. Lien « Mon compte » ajouté au header studio. /projects délié (route existe encore).
- ✅ Verts (#d9ffd0) → rouge (#fc1c46) sur toutes les pages React (Dashboard, Admin, Auth, ForgotPassword, ResetPassword, ProtectedRoute, AuthCallback).
- ✅ Onboarding studio v3 : overlay noir, progress cramoisie, gros chiffres info (2×, 80 %, 45 min), options pill animées (stagger), écran final avec barres d'onde animées + dropzone v3. Textes réécrits stop-slop (sans IA, sans tirets cadratins).
- ✅ Modal « Versions du morceau » (bkPop) refait v3 (.bk-box/.bk-row, boutons ghost pill) + purge derniers tokens old-style (paywall, trial-cap, webview banner, trial banner → var(--void)/var(--hair-2)/var(--graphite)).
- Cache CSS → ?v=13.16. Testé : iteration_29 (100% PASS batch précédent) + screenshots dashboard/versions/landing pour les retours visuels.
- Guide d'écriture user : /app memory — règles stop-slop (pas d'adverbes, voix active, pas de « — », direct).

## Backlog restant
- P2 : Tester sur iPhone (menu latéral + export complet Safari).
- P4 : Pré-remplir la recherche de vidéos gratuites selon le style choisi à l'onboarding.
- P5 : Jauge de stockage utilisé dans le compte.
- Futur : tracker vignettes manquantes par navigateur (admin).

## Mobile CapCut-like + onboarding login + badges clips (21 août 2026, suite)
- ✅ Toggle thème sans emoji : SVG soleil/lune (landing paintTheme + studio paintThemeBtn) + meta theme-color dynamique (metaTheme / metaThemeL) + html,body{background:var(--void)} → plus de bandes noires en mode clair iOS. Studio.js (parent iframe) synchronise fond + theme-color via bc_theme (interval 1.5s).
- ✅ Éditeur mobile : bouton Plein écran = icône seule (#fsLb masqué ≤700px, setFsLabel()), barre CapCut en bas (#mobBar redevenu barre basse fixe avec icônes SVG Clips/Son/Paroles/Style/Plus, drawer supprimé pour mobBar — #homeTabs reste en tiroir), page + panneaux s'arrêtent à calc(60px + env(safe-area-inset-bottom)) → rien sous la barre Safari.
- ✅ Onboarding à la première connexion : backend onboarding_done default False (ligne ~334), Google insert False, seeds demo/admin True. Nouveau compte (même après suppression) → Dashboard redirige /studio → onboarding. Testé par API (register → me → onboarding_done=False → delete).
- ✅ Flux création mobile (≤900px) : newMorceau() → mobImportFlow() plein écran Étape 1/2 « Dépose ton son » (esthétique onboarding) → Étape 2/2 « Ajoute tes clips » (multi, jusqu'à 24, bouton Banque de vidéos gratuites) → éditeur. data-testid mob-import-*.
- ✅ Badges « Optimisation en arrière-plan » remplacés par une barre de chargement rouge discrète en bas du clip (.clip-load : % d'envoi ou animation indéterminée, tooltip conserve le libellé). Badge d'échec (clip-fail) passé du jaune au cramoisi.
- Cache CSS → ?v=13.17. Auto-testé : screenshots mobile 390×844 (flux import + barre CapCut barTop=784/844) + desktop (fsBtn OK) + API onboarding.

## Retours mobile v2 + paywall + filigrane différé (21 août 2026, soir)
- ✅ Barre CapCut mobile : marge Safari accrue → hauteur/paddings avec max(env(safe-area-inset-bottom),16px) (barre à 76px du bord, vérifié barTop=768/844).
- ✅ Bandes noires landing (mode clair) : Landing.js synchronise fond parent + meta theme-color via bc_theme (comme Studio.js), iframe background transparent. Vérifié parent = blanc.
- ✅ Fin d'onboarding = mêmes écrans que le flux nouveau son : mobImportFlow('clips') remplace showOnbVideoPrompt (fonction conservée mais plus appelée) ; bouton Banque compatible desktop.
- ✅ Paywall export redesigné v3 (.pw-*) : eyebrow [EXPORT], titre fort, 3 features à puces carrées cramoisies, CTA halo « Débloquer · 7 jours offerts », note prix, 3 alternatives discrètes (Essentiel/Pro annuel/Studio), Plus tard + clés EN ajoutées au dict.
- ✅ Studio mobile : #exportBtn réduit (7px 12px, 10.5px), #fsBtn rond 38px icône centrée.
- ✅ FILIGRANE DIFFÉRÉ : drawWatermark seulement si tier free ET wmArmed() (localStorage bc_wm_armed OU user.onboarding.wm_armed serveur). armWatermark() appelé au 1er showPaywall (clic Exporter) → filigrane appliqué pour toujours ensuite. Backend /api/onboarding accepte wm_armed. Vérifié : wmArmed False avant, True après paywall.
- Cache CSS → ?v=13.18.

## Fix scroll mobile Chrome (21 août 2026)
- ✅ /studio (wrapper React) : h-screen (100vh) → position:fixed + height:100dvh + overflow hidden sur html/body pendant le montage. Vérifié scrollH==innerH (844/844). L'interface d'édition tient entièrement à l'écran sur Chrome et Safari mobile.

## Login bloqué + redirection morceaux + plein écran mobile + tuto (21 août 2026)
- ✅ « Connexion en cours » en boucle : timeout 15s sur POST /auth/login + en cas d'échec/réponse perdue, refreshUser() vérifie si le cookie est posé et redirige quand même. checkAuth retourne désormais les données.
- ✅ Après connexion (email, Google, callback) → /studio (Mes morceaux) au lieu de /dashboard (AuthPage, AuthContext.loginWithGoogle, AuthCallback).
- ✅ Plein écran mobile : body.is-fs (posé par setFsLabel) masque #mobBar et supprime le padding bas. Vérifié display:none en fullscreen.
- ✅ Tuto mobile réécrit, précis, différent du desktop : 8 étapes ciblant chaque onglet de la barre basse (Son/Clips/Paroles/Style/Plus), timeline, Exporter + clés EN.
- ✅ Bouton « Revoir le tutoriel » dans le panneau Plus (restartMobTuto()).
- Cache CSS → ?v=13.19.

## Waveform mobile landing (21 août 2026)
- ✅ La waveform animée du héro s'affiche désormais aussi sur mobile (≤960px) : bande pleine largeur en bas du héro, opacité .45, masque dégradé latéral. Vérifié 390px.
- Info donnée au user : réception email contact@beat-cut.com via Cloudflare Email Routing (gratuit, compatible Resend qui n'utilise pas les MX) + Gmail send-as via smtp.resend.com.

## Adresse contact@beat-cut.com généralisée (21 août 2026)
- ✅ jules.beatcut@gmail.com remplacé partout par contact@beat-cut.com : LegalLayout (CONTACT_EMAIL → toutes pages légales), Dashboard (démo Studio), paywall studio.html.
- ✅ Emails Resend : reply_to=contact@beat-cut.com ajouté (expéditeur reste no-reply@beat-cut.com) → les réponses des utilisateurs arrivent dans la boîte IONOS du user.
- Boîte créée par le user chez IONOS (Mail Basic inclus, MX auto).

## Prix Studio masqué + Jauge stockage (21 août 2026)
- ✅ Prix Studio retiré des pages publiques : landing (« Sur mesure »), Dashboard (« Planifier une démo » seul), CGV (« sur devis »), paywall (déjà « Sur démo »). Admin/AffiliateAdmin gardent le label interne.
- ✅ GET /api/me/storage : somme GridFS (media.files, metadata.user_id) + limites d'affichage par plan (free 2 Go, basic/essentiel 15 Go, pro 50 Go, studio 100 Go — indicatif, non bloquant).
- ✅ Carte « Stockage » dans Mon compte (data-testid storage-card) : barre rouge, X utilisés sur Y, nb fichiers. Testé API (12 Mo/15 Go pour demo) + screenshot.

## Fix déconnexion login Google (21 août 2026)
- ✅ RCA : /auth/google/session ne faisait pas register_sid() (contrairement au login/register email) → avec la protection anti-partage (_check_sid, limite 1 appareil), tout compte ayant déjà des sids était rejeté au premier /auth/me → déconnexion immédiate après login Google.
- ✅ Fix : register_sid(user, session_token) ajouté dans google_session. Testé par simulation (ancien sid présent → nouveau token accepté, éviction de l'ancien conforme à la limite).
- ⚠️ PROD : correctif présent en preview seulement — nécessite un redéploiement pour beat-cut.com.

## Fix n°2 déconnexion Google : vieux cookie masquant (21 août 2026)
- ✅ RCA finale : get_current_user lisait access_token (JWT email périmé) EN PREMIER et levait 401 « autre appareil » sans essayer session_token (Google, valide). Tout utilisateur ayant un ancien login email sur le même navigateur était déconnecté ~2s après le login Google.
- ✅ Fix : get_current_user essaie toutes les branches (jwt cookie → session cookie → bearer) avant de lever le 401 conflit ; google_session supprime le cookie access_token obsolète.
- ✅ Testé curl : vieux jwt + session google valide = 200 (avant 401) ; session écrasée seule = 401 (anti-partage intact) ; login normal = 200.
- ⚠️ REDÉPLOIEMENT REQUIS pour beat-cut.com.

## RCA prod login bounce + readiness (21 août 2026, nuit)
- ✅ RCA deployer (prod) : les visiteurs sur www.beat-cut.com appelaient l'API en absolu sur l'apex (beat-cut.com) → cross-origin, cookies non honorés → /auth/me 401 → bounce /login. Le build prod avait bien les fixes sids.
- ✅ Fixes appliqués : api.js baseURL relatif '/api' quand origine ≠ REACT_APP_BACKEND_URL ; CORS élargi automatiquement aux jumeaux www/apex ; COOKIE_DOMAIN optionnel (env) sur tous les cookies (set + delete via clear_auth_cookies) ; URLs d'emails → APP_URL (env, ajouté au .env preview) ; .gitignore débloqué (.env patterns retirés).
- ✅ Code review : fix funnel essai Stripe — checkout avec trial renvoie payment_status="no_payment_required" : désormais accepté (webhook checkout_completed, poll /payments/status qui renvoie "paid" normalisé, réconciliation).
- ⚠️ BACKLOG (code review HIGH confirmé, non traité) : bonus parrainage « +1 mois offert » jamais réellement accordé (current_period_end écrasé par la sync Stripe ; bonus_until jamais lu). À reconcevoir via coupon Stripe ou lecture de bonus_until dans sub_info.
- ✅ Deployment readiness re-run : PASS (aucun bloqueur).
- ACTIONS USER pour la prod : ajouter secrets APP_URL=https://beat-cut.com, COOKIE_DOMAIN=.beat-cut.com, CORS_ORIGINS=https://beat-cut.com,https://www.beat-cut.com puis REDÉPLOYER.

## Secrets prod rendus inutiles (21 août 2026)
- ✅ cookie_domain_for(request) : Domain=.beat-cut.com déduit du Host (x-forwarded-host prioritaire) pour tout domaine custom ; None pour *.emergentagent.com/localhost. COOKIE_DOMAIN env prime si défini. Tous les set/delete cookies passent request (register, login, google_session, logout, delete_account) ; clear_auth_cookies supprime sur les deux domaines (avec et sans Domain).
- ✅ CORS_ORIGINS fallback '*' si vide (Starlette renvoie l'origine exacte avec credentials) + jumeaux www/apex auto.
- ✅ APP_URL défaut https://beat-cut.com (surchargé en preview par .env).
- → L'utilisateur n'a AUCUN secret à ajouter : il suffit de redéployer.

## Point login Google prod (21 août 2026, fin de soirée)
- Diagnostic complet : la prod tourne le dernier build (vérifié fichier par fichier : cookie_domain_for, api.js same-origin, device_conflict, register_sid). Flux front relu ligne à ligne (loginWithGoogle conforme playbook, AuthCallback POST via api relatif, App.js intercepte #session_id avant le routing).
- Logs prod : dernières tentatives Google à 17:05-17:07, AVANT le redeploy correctif de 18:54. Aucune tentative Google depuis → le bug rapporté concernait l'ancien build ; la version corrigée n'a jamais été testée avec Google.
- EN ATTENTE : re-test utilisateur de la connexion Google sur beat-cut.com. Si échec : demander statut du POST /api/auth/google/session + corps du 401 de /auth/me (« Non authentifié » = transport ; « autre appareil » = anti-partage).

## Fix final boucle login Google — conformité playbook (21 août 2026, nuit)
- RCA consolidée (deployer + playbook Emergent Auth) : les google/session prod renvoyaient 401 upstream = ticket à usage unique REJOUÉ (rechargement/double navigation) → catch → bounce /login en boucle.
- ✅ App.js : détection du callback via useLocation().hash (réactif) au lieu de window.location.hash (déviation playbook corrigée).
- ✅ AuthCallback : filet anti-rejeu — si l'échange échoue, GET /auth/me ; si session valide → setUser + /studio (testé : ticket bidon → reste connecté sur Mes morceaux, hash purgé). decodeURIComponent(ticket) + purge du hash en cas d'échec.
- ✅ Cookie session_token → SameSite=Lax (Safari mobile) ; logging détaillé du 401 upstream (UA, corps) dans google_session ; liens landing /login,/cgv,... target=_top (sortie d'iframe).
- ⚠️ REDÉPLOIEMENT REQUIS pour beat-cut.com.

## Newsletter admin (21 août 2026, suite)
- ✅ Onglet NEWSLETTER dans /admin (tabs TABLEAU DE BORD / NEWSLETTER, composant NewsletterAdmin.js).
- ✅ Rédaction : mode Éditeur (gabarit DA v3 noir/cramoisi) ou import HTML brut ; aperçu iframe ; envoi test à un email.
- ✅ Envoi à toute la base (users avec newsletter != false, défaut inscrit) en tâche de fond, 0,6 s entre chaque envoi (limite Resend), suivi progression en live.
- ✅ Liste de diffusion : recherche + cases à cocher pour exclure/réinscrire un email (POST /admin/newsletter/subscription).
- ✅ Taux d'ouverture : pixel GET /api/newsletter/open/{campaign}/{uid} ($addToSet opened_by) + tableau campagnes (envoyés, ouvertures, taux, statut).
- ✅ Lien de désinscription légal dans chaque email : GET /api/newsletter/unsubscribe?u={user_id} (page HTML noire).
- ✅ Case newsletter à l'inscription (AuthPage, cochée par défaut, champ RegisterIn.newsletter) — vérifié en DB.
- Collection Mongo : newsletter_campaigns {campaign_id, subject, mode, recipients, sent, failed, opened_by[], status, created_at}.
- Testé : login admin, subscribers (193), toggle, preview, pixel, unsubscribe, register newsletter=false. PAS d'envoi réel à la base (clés live).

## Page d'aide /aide (21 août 2026)
- ✅ /app/frontend/src/pages/Aide.js : guide complet FR (pages du site, 4 étapes, barre du haut PC, panneaux Clips/Son/Paroles/Style, timeline, studio mobile CapCut, série de vidéos, export, raccourcis clavier) + sommaire ancré + CTA contact. Responsive mobile/PC, zéro emoji.
- ✅ Liens ajoutés : Navbar desktop+mobile ("Aide"), Footer React, footer landing.html, footer studio.html, bouton "Aide & guide complet" dans le menu Plus mobile du studio.
- Route publique /aide dans App.js.

## Emails prod jamais partis + fix rappel essai (21 août 2026, soir)
- RCA deployer : RESEND_API_KEY VIDE dans les secrets de prod → TOUS les emails (fin d'essai, bienvenue, reset, newsletter) étaient en "[EMAIL simulé]" en prod. ACTION USER : remplir RESEND_API_KEY (et vérifier SENDER_EMAIL="BeatCut <no-reply@beat-cut.com>") dans Deploy → Secrets puis redéployer. STRIPE_WEBHOOK_SECRET aussi vide (webhook à réactiver via bouton admin après redeploy).
- ✅ Fix code : trial_reminder_sent n'est plus marqué True si send_email échoue (webhook _wh_trial_will_end + _trial_reminder_loop) → les rappels seront retentés au passage suivant une fois la clé posée.
- Limite : les users dont le flag a déjà été posé à tort en prod ne seront pas rattrapés (essais probablement déjà terminés).

## Fix popup BPM mobile (22 août 2026)
- Bug : sur mobile, clic sur la puce BPM → rien ne s'affichait. Cause : .transport{overflow:hidden} (mobile) clippait .bpm-pop (position:absolute au-dessus de la puce).
- ✅ Fix CSS (media query mobile, studio.html ~l.469) : .bpm-pop en position:fixed centré (top:36%, translate(-50%,-50%), width:min(280px,88vw), z-index:500).
- Vérifié par screenshot mobile 390px : popup visible avec -1/+1, saisie, ÷2/×2, TAP. Redéploiement requis pour prod.

## Relances lifecycle (22 août 2026)
- ✅ POST /api/telemetry/paywall : le studio l'appelle dans showPaywall() → users.paywall_seen_at (1re fois) + paywall_seen_count.
- ✅ Relance paywall : email "Ta vidéo est prête" (CTA /studio) aux comptes gratuits ayant vu le paywall il y a 2 h à 7 j, sans abonnement — envoi unique (paywall_relance_sent), respecte newsletter=False + lien de désinscription.
- ✅ Relance sans export : email "Ta première vidéo t'attend" aux inscrits 24-72 h sans aucun clic Exporter (ni export_logs ni paywall_seen_at) — envoi unique (noexport_relance_sent).
- ✅ Boucle horaire _lifecycle_relance_loop (startup) + déclencheur manuel POST /api/admin/relances/run (renvoie les compteurs).
- Testé e2e : 2 users fictifs (julesfar17+paywall / +noexport@gmail.com) → 1 email chacun réellement envoyé via Resend, flags posés, ciblage correct, telemetry paywall OK. Nettoyé après test.
- Fenêtre 24-72 h volontaire : pas de blast rétroactif sur l'ancienne base.

## Stats relances admin + aide EN (22 août 2026)
- ✅ GET /api/admin/relances/stats : par type (paywall, noexport, reengage_d3, reengage_d7) → envoyées / converties (tier != free aujourd'hui) / taux + compteur paywall_seen.
- ✅ Admin.js : section "Relances automatiques" (tableau + bouton LANCER LES RELANCES MAINTENANT via POST /admin/relances/run).
- ✅ Aide.js réécrite bilingue : CONTENT {fr, en} sélectionné via useI18n().lang (détection navigateur + bouton FR/EN existant). Testé screenshot : h1 EN "Understand everything about BeatCut."
- ✅ Google login prod : CONFIRMÉ RÉSOLU par l'utilisateur (redirect /dashboard + anti-rejeu).

## Perf aperçu : 3 bugs critiques corrigés (22 août 2026) — build v13.10-perf
Symptôme user : "gros bugs sur l'aperçu, lent, pas de fps". Télémétrie : 1107 frame_miss, 48 decoder_error "codec non supporté", 35 preview_stall.
1. drawPreview comparait wcA.clip===cl.wc alors que le lecteur joue le PROXY (cl.wcProxy, introduit en v13.08) → dès qu'un proxy existait, AUCUNE frame décodée n'était affichée (vignettes figées). Fix : accepte wcA.clip===cl.wcProxy||cl.wc.
2. Télémétrie preview_stall référençait `wp` inexistant → ReferenceError dans drawPreview → mort de la boucle rAF (image figée, son continue). Fix : wp défini + try/catch autour de drawPreview dans raf() (TEL raf_error).
3. Verrous metadata.proxy_processing/processing orphelins après restart/deploy → génération de proxy bloquée À JAMAIS (users iPhone HEVC = 48 "codec non supporté" sans proxy → rien ne joue). Fix : cleanup au startup backend. Vérifié : proxy clipA généré en 15 s après déblocage.
NB : le navigateur headless de test n'a pas les codecs H.264 → vérification visuelle de la lecture impossible en local, validation par télémétrie/logs. REDÉPLOIEMENT REQUIS.

## Fix lecture mobile qui ne démarre pas (22 août 2026, soir)
- Cause : play() et startLoop() ne faisaient JAMAIS audioCtx.resume(). Sur iOS l'AudioContext est 'suspended' (surtout à la réouverture d'un projet sauvegardé : contexte créé hors geste utilisateur) → aucun son, currentTime figé → l'aperçu semble ne pas se lancer.
- ✅ Fix : resume() SYNCHRONE dans togglePlay()/toggleLoop() (dans le geste), re-résume await après warmUpPlans, toast "Touche encore une fois" + télémétrie audioctx_suspended si toujours bloqué.
- Vérifié : lecture démarre (playing:true, timecode avance) sur viewport mobile, 0 erreur JS. iOS réel à valider par l'utilisateur après redéploiement.

## Boucle login Google (retour) — VRAIE cause : anti-partage limite 1 (22 août 2026, soir)
- RCA deployer prod : google/session 200 OK, cookie posé, MAIS /auth/me 401 intermittents. Cause : _session_limit()=1 pour tous (3 seulement pour Studio) → chaque login (tel/PC/2e onglet) évince l'autre appareil → ping-pong de déconnexions. Indépendant des déploiements (d'où la "réapparition").
- ✅ Fix : limite 3 appareils (5 Studio, 99 admin/VIP) ; logs WARNING sur chaque rejet anti-partage (_check_sid + get_current_user) ; migration unique meta:sid_limit_migration_v2 (vide les sids existants) ; purge des user_sessions expirées au startup (2676 docs en prod).
- ✅ Testé e2e : 3 logins simultanés → 3× /me 200 ; 4e login → appareil 1 éjecté (401). REDÉPLOIEMENT REQUIS.
- L'ancien bug /studio statique reste corrigé (redirect /dashboard) — ne pas y retoucher.

## Durcissements post-boucle Google (22 août 2026, nuit)
- ✅ studio.html API.init() résilient : 3 tentatives /auth/me (backoff 600ms), redirection login SEULEMENT après 2 vrais 401 — une erreur réseau/CDN passagère ne déconnecte plus.
- ✅ register_sid atomique ($push + $slice) : deux logins simultanés ne s'écrasent plus (testé : 3 logins parallèles → 3 /me 200).
- IMPORTANT : l'utilisateur a retesté AVANT la fin du déploiement asynchrone du fix limite-3. Lui demander de tester après la fin du déploiement suivant (qui inclut aussi ces durcissements).

## Re-vérification complète chaîne Google (22 août 2026, nuit)
Tous les maillons audités + testés en préview :
1. loginWithGoogle → redirect /dashboard (pas /studio statique) OK
2. App.js intercepte #session_id avant routing OK ; AuthContext saute checkAuth si hash présent OK
3. AuthCallback : échange + filet anti-rejeu /me OK (testé : ticket consommé + session valide → /studio connecté)
4. google/session : faux ticket → 401 propre ; cookie session_token SameSite=Lax Domain=.beat-cut.com OK
5. get_current_user : JWT→session→Bearer, conflit loggé OK ; _user_from_session expiry OK
6. Limite 3 appareils + $push atomique + migration sids OK (3 logins parallèles cohabitent, 4e éjecte le plus ancien)
7. api.js : retry transport 520/502 sur /auth/* OK ; studio API.init 3 tentatives OK
8. Session simulée (cookie session_token) : /dashboard et /studio restent connectés 8 s+, API.user OK
Reste à faire par l'utilisateur : REDÉPLOYER (les fixes limite-3 + atomique + init résilient ne sont pas encore en prod), attendre la FIN du déploiement, tester Google tel+PC.

## Fix cookies en doublon (indice "marche en navigation privée") — 22 août 2026, nuit
- Cause probable de la boucle Google en navigation normale : DEUX cookies du même nom (ancien host-only + nouveau Domain=.beat-cut.com) — le serveur ne lisait que le premier (request.cookies) → si périmé → 401 → boucle. Navigation privée = pas de vieux cookie = OK.
- ✅ _cookie_values() : get_current_user essaie TOUTES les valeurs de access_token et session_token.
- ✅ set_jwt_cookie / set_session_cookie purgent le doublon host-only avant de poser le cookie de domaine.
- Testé : périmé+valide (2 ordres) → 200 ; vieux JWT + session valide → 200 ; périmé seul → 401. REDÉPLOIEMENT REQUIS.

## Lot 4 chantiers studio (23 août 2026) — build v13.11-crop
1. BUG "nouvelle version au clic sur un morceau" : restoreIncomplete jamais activé → chaque addClip pendant la restauration sauvait un état PARTIEL qui écrasait le bon (relégué dans Versions). Fix : verrou actif pendant toute la restauration, restoreFails compte les fichiers manquants (sauvegarde suspendue + toast si échec), reset dans newMorceau. Testé : restore complet → verrou levé, "Saved".
2. BUG vignettes : _wcMakeThumbsNow utilise le PROXY en priorité (plus fiable/léger) ; à l'arrivée du proxy, TOUTES les vignettes manquantes sont régénérées (plus seulement si liste vide). Non vérifiable visuellement en headless (pas de codecs H.264) — chemin de code validé.
3. FEATURE recadrage : clip.crop {x,y} (-1..1) appliqué au cover-fit (frame décodée + vignette fallback + export via même code). UI desktop : bouton "Recadrer" par clip (sliders H/V + Centrer). UI mobile : bouton Recadrer dans la feuille "Ce plan". Persisté dans clipRefs.crop, restauré au chargement. Testé : crop {x:0.6} appliqué + sauvegardé.
4. FEATURE popup mobile "BeatCut marche mieux sur PC" : maybePcHint() après son+clips importés (pas au restore), 1 fois par appareil (localStorage bc_pc_hint), DA v3, bouton "Continuer quand même", FR/EN (attention : les clés du dict EN doivent utiliser l'apostrophe DROITE, T() normalise ’→'). Testé FR + EN.
REDÉPLOIEMENT REQUIS.

## Recadrage tactile par plan (23 août 2026) — build v13.12-cropdrag
- Clic sur un plan → 2 nouvelles options partout : "Voir le plan" (lecture du plan seul avec arrêt auto) et "Recadrer le plan" (drag).
- Desktop : boutons dans #planPop (testids plan-view-btn-pop / plan-crop-drag-btn-pop). Mobile : dans la feuille "Ce plan" (plan-view-btn / plan-crop-btn). Les sliders par clip restent dans le panneau Clips (desktop).
- Mode recadrage : overlay #cropOv sur #stageWrap (pointer events souris+tactile, setPointerCapture), on glisse l'image → plan.crop {x,y} clampé, mapping 1:1 pixel (excès de cover-fit), boutons Centrer / Terminé (dirty() à la sortie), exitCropMode() appelé par play().
- Priorité de recadrage : plan.crop || clip.crop, appliquée frame décodée + vignette + export (même code). rebuildPlans préserve crop. Persisté via M.plans.
- Testé e2e mobile : drag → {x:0.413}, Centrer → null, Terminé → fermé+Saved, Voir le plan → lecture + arrêt auto. REDÉPLOIEMENT REQUIS.

## Zoom dans recadrage + docteur vignettes (23 août 2026, soir) — build v13.13-zoomcrop
- "Ça fonctionne pas" (recadrage) : cause identifiée = clip déjà 9:16 → aucun excès à glisser. Fix : ZOOM (plan.crop.z 1→2.5) via curseur (100-250%), molette et pincement 2 doigts. Draw : s=cover*z (aperçu + vignette + export). Centrer remet tout à zéro.
- Vignettes : thumbDoctor() — passe toutes les 3 s (12 max) tant qu'il manque des vignettes, relance wcMakeThumbs(missing) par clip (_thumbBusy anti-concurrence), déclenché après chaque makeThumbs.
- Vérifié e2e : slider z=2, drag zoomé {x:.11,y:.25,z:2}, molette z=2.45, Centrer→null. Prod servait bien v13.12 (pas de cache CDN, header no-store). REDÉPLOIEMENT REQUIS pour v13.13.


## 2026-06 — Fix double décompte du compteur d'export
- Cause : `/api/telemetry/export` (envoyé à chaque fin d'encodage) écrivait dans `export_logs`, la collection du quota → 1 export comptait 2 (intermittent car fetch fire-and-forget).
- Fix : télémétrie déplacée dans `db.export_telemetry` ; migration au démarrage (`export_telemetry_split_v1`) qui purge les anciens logs télémétrie d'`export_logs` (corrige rétroactivement les quotas clients) ; index `(user_id, created_at)` sur `export_logs`.
- Testé via curl : télémétrie → quota inchangé ; register → +1.


## 2026-06 — Fiabilisation de la sauvegarde automatique des projets (perte de montages)
Causes racines trouvées : (1) sauvegarde 100 % serveur sans filet local, échecs 401 (session expirée / anti-partage 3 appareils) et 429 (limite projets Free=1) signalés uniquement par un petit label ; (2) requêtes de save croisées (mobile) → ancienne écrase récente ; (3) course à l'ouverture d'un projet (état vide envoyé avant le chargement) ; (4) purge GridFS des médias non référencés après 24 h → vidéos supprimées si le projet n'a jamais été sauvé ; (5) clip sans mediaId ignoré au rechargement → indices de plans décalés.
Fix :
- Backend `save_project` : `client_id`+`seq` (une seq plus ancienne du même onglet → `stale:true`, pas d'écrasement) ; `_state_is_empty` → 409 `empty_overwrite` si un état vide veut remplacer un montage ; `_log_save_failure` → collection `save_failures` ; `POST /api/telemetry/save-failed` (auth facultative) ; `GET /api/admin/telemetry/save-failures?days=` ; marge nettoyage GridFS 24 h → 7 jours.
- Studio (`studio.html` bloc « Sauvegarde fiabilisée ») : saves sérialisées, retry exponentiel (2→30 s), flush `keepalive` sur pagehide/visibilitychange, flush avant changement de morceau, `canPersist()` bloque si projet distant non chargé, `restoreIncomplete=true` posé AVANT le GET, brouillon IndexedDB (`bc_drafts`) restauré silencieusement si plus récent/complet que le serveur, écran bloquant style tuto (`save-block-overlay`) pour 401 (bouton reconnexion + « Je suis reconnecté ») / 429 (liste des projets avec Supprimer + lien tarifs) / offline / serveur ; remap des indices de plans si clip manquant + modal `missing-clips-modal` mettant en avant « Récupérer mes vidéos ».
- Admin React : section `SaveFailuresAdmin` (par raison + par utilisateur).
- Testé : iteration_31.json (100 % backend/frontend).


## 2026-06 — Partage direct après export
- Bouton « Partager » dans la modale « Ta vidéo est prête » (`dl-share-{i}`) : Web Share API niveau 2 (`navigator.share({files})`) → feuille de partage du téléphone (TikTok / Instagram / WhatsApp…). Affiché seulement si `canShare` avec fichier est supporté (iOS Safari, Chrome Android) ; masqué sur desktop et pour les .zip de série. Le partage réussi décompte l'export comme un téléchargement ; annulation (AbortError) = rien. Testé via screenshot avec API simulée (fichier mp4 transmis, export compté).


## 2026-06 — Tap for cut, Vidéo hook, plans sans doublons
- **Plans sans doublons** (`assignPlansSmart`, studio.html) : stock = tous les (clip, seek) ; pour chaque plan, score = distance au même moment ×10000 + distance au même clip ×100 + écart de timecode avec les voisins du même clip, forte pénalité si voisin direct = même clip. Utilisé par rebuildPlans, autoAssign, Mélanger, removeClip, « Autre plan » mobile. Vérifié : 6 moments → 12 plans sans répétition avant épuisement, 0 voisin même clip.
- **Tap for cut** (bouton timeline `tap-cut-btn` + menu Plus mobile) : overlay style tuto, vitesse 100/75/50 %, grille 1/½/¼/⅛ temps, décompte 3-2-1, taps écran/Espace (latence sortie compensée), quantize, remplace toutes les coupures ; plans verrouillés → clip transféré au plan le plus proche, verrou conservé. Testé en page (taps simulés → quantize ⅛ exact, verrou conservé).
- **Vidéo hook** (page `#/hook`, nav desktop + onglet mobile + menu Plus + bouton Hook éditeur) : choix du morceau (serieLoadMorceau), import vidéo (WebCodecs, sinon transcodage serveur), son du hook décodé et équilibré (RMS), musique d'avant l'extrait sous passe-bas (300 Hz, 35 %) → ouverture 0,5 s avant la fin → drop pile à la fin du hook. Mode avancé : rognage, volumes, passe-bas, durée d'ouverture, musique (avant l'extrait / l'extrait), instrumentale (passe-bas / séparation IA Demucs `stem=instrumental`, Pro). Aperçu temps réel (hook + enchaînement montage) et export via `exportVideo(..., hook={dur,audio,draw})` : `exportOffline` accepte un préroll (frames hook via `wcSeekFrame`, mix OfflineAudioContext). Backend : `POST /api/separate` accepte `stem` (vocals|instrumental).
- Export hook non testable en headless (pas d'encodeur AVC) : logique testée par morceaux (frames WC, mix offline 9 s = 3+6, niveau plein au drop).

- **Sous-titres du hook** : après import, transcription automatique du dialogue (Groq/Whisper via `/api/proxy/transcribe`, langue = sélecteur paroles) → `HOOK.words` (temps hook) ; dessinés avec le style de sous-titres du morceau via `hookDrawSubs` (swap temporaire de `M.words` → `drawLyricBlock`) en aperçu et à l'export ; bouton ON/OFF + « Retranscrire », texte visible sous l'import. Testé en page (appel API réel + rendu pixels + toggle).

- **Correction des mots du hook** : chips cliquables (`hook-word-{i}`) → input en place (Entrée valide, vide = supprime, Échap annule), redessin immédiat.
- **Hook dans Série** : page Série affiche « Ajouter mon hook à chaque vidéo » (`serie-hook-toggle`) si un hook est chargé pour le morceau sélectionné (`hookReadyFor`) ; `exportKept` prépare le préroll UNE fois (`hookInstrReady` + `hookPrepareExport`) et le passe à chaque `exportVideo(..., hk)` ; suffixe `-hook-vN`. Lien « Utiliser ce hook sur une Série » depuis la page Hook. Testé en page (édition/suppression de mot, toggle Série, préroll réutilisable : mix 7 s = 3+4, sous-titres dessinés).

- **Hook mémorisé** : `M.hook={mediaId,name,dur,trim,vol,mus,lp,fade,src,instr,subs,words}` inclus dans l'état projet (`buildStateDoc`/`fetchRemoteMorceau`) ; vidéo hook envoyée en GridFS en arrière-plan (`hookPersistUpload`), `hookSave()` à chaque réglage/mot/toggle ; `hookRestore(m)` au choix du morceau / ouverture de la page Hook / bouton « Charger le hook mémorisé » en Série ; « Retirer le hook de ce morceau ». Backend `_project_media_ids` référence `hook.mediaId` (pas de purge GridFS). Testé bout en bout (sauvegarde serveur → rechargement → restauration réglages + mots).

- **Fix freezes export hook + refonte UI Hook** : cause = hook lu depuis le fichier brut (MOV iPhone : edit list / VFR / HEVC → timestamps non normalisés → images figées) et repli `<video>` lent. Désormais la vidéo hook passe TOUJOURS par le pipeline clips (upload GridFS + transcodage serveur, version optimisée récupérée pour WebCodecs) ; avant export : contrôle de décodage (3 frames, 6 s max chacune) ; pendant l'export : détection de gel (même frame > 0,8 s) → export ANNULÉ avec message clair, rien de décompté ; plus de repli `<video>` à l'export (export désactivé si non décodable, message). UI : parcours 3 étapes (Morceau → Vidéo hook → Écouter & exporter), cartes, aperçu cliquable avec bouton play, barre Hook/DROP/Montage, bouton export désactivé + explication tant que tout n'est pas prêt, carte fichier (Changer/Retirer), mode avancé replié. Testé en page (états vides/chargé, gel simulé → annulation, desktop + mobile). Résidus de projets de test supprimés du compte démo.

- **Fix freezes export (coupes très rapprochées)** : `wcExportSeek` faisait un reset/configure du décodeur à CHAQUE changement de plan → rafale de resets avec des coupes ⅛ temps → décodeur (HW) en erreur → `pl.err` jamais effacé → plus aucune frame → repli `<video>` figé pour le reste de l'export. Fix : re-seek seulement si autre clip / retour arrière / saut > 1 s ; `SegPlayer.recover()` (décodeur neuf en `prefer-software`) + re-seek si frame manquante ou erreur ; télémétrie `export_frame_recover` / `export_frame_missing`. Même logique pour le hook (`wcSeekFrame`). Test : 80 plans de 50 ms sur 2 clips, 120 frames → 0 manquante, 0 figée, 0 imprécise, ~6 ms/frame ; récupération après erreur OK.

- **Fix export hook iPhone « image manquante à 0.0 s »** : cible 0 alors que la 1re image décodée est à t>0 (edit list / délai B-frames du fichier transcodé) → `frameAt` attendait 12 s puis null. Fix : `parseWC` normalise les cts (1re image à 0) + `frameAt` prend la 1re image disponible si la cible la précède. Vérifié (29 ms au lieu de 12 s + échec).
- **Page Hook mobile façon studio** (≤700px, body.mob-hook) : barre haute (retour · titre + « Étape X/3 » · Exporter), aperçu plein écran au milieu (tap = lecture/stop, ferme les panneaux), barre Hook/DROP/Montage, barre basse 5 boutons (Morceau · Hook · ▶ · Réglages · Sous-titres) ; les cartes Morceau/Hook/Réglages deviennent des panneaux coulissants (`.hk-sheet`, un seul ouvert, `hookMobSheet`). Après choix du morceau → panneau Hook ouvert auto ; après import → panneaux fermés pour voir l'aperçu.

- Aperçu Hook mobile centré (`hookFitStage` : canvas dimensionné au ratio du format dans la scène, recalcul au resize) ; bouton admin « Revoir tuto » déplacé dans un menu ⋯ de l'en-tête (`admin-menu-btn` → Revoir le tuto & questionnaire / Tableau de bord admin).

- Curseur personnalisé (point + anneau) supprimé partout : studio.html (script + v3-skin.css) et React (index.js + index.css) → curseur système normal.

- **Freezes aperçu avec coupes rapprochées (tous navigateurs)** : cause = à chaque plan, re-seek d'un décodeur (reset + décodage depuis la keyframe, 100-300 ms sur décodeur matériel 1080p) → impossible avec des plans ≤ 340 ms → image figée. Fix = **cache de coupes** (`cutCache`, `SHORT_PLAN=0.34`) : une ImageBitmap (≤ 720 px) par (clip, seek) des plans courts, décodée en arrière-plan (`cutCacheBuild`, lancé au warm-up et 1,2 s après chaque modif) ; à la lecture les plans courts affichent l'image du cache, les 3 décodeurs live (`wcPrepLong`) ne se préparent que sur les prochains plans LONGS ; secours : si un décodeur n'est pas prêt, image du cache plutôt qu'un gel. Simulation latence 250 ms : avant = 211 frames identiques (gel total), après = 3 max. Invalidation sur removeClip/resetAudioState.
- **Firefox : vignettes timeline toutes identiques** : `seedThumbs` posait le même poster sur tous les slots ; le repli `<video>` de `_wcMakeThumbsNow` ne complétait que les slots VIDES (pas les posters) → identiques à vie. Fix : slots « seeded » traités comme manquants, repli attendu, `makeThumbAtTag` efface le flag poster.

## 2026-06 — Coupes rapprochées : ANNULATION de l'image fixe, pool de décodeurs
- **Régression signalée** : le « cache de coupes » affichait volontairement UNE image fixe pour tout plan < 340 ms → l'utilisateur ne voyait que des images figées sur les coupes rapides. Approche abandonnée.
- **Nouveau moteur** (`studio.html`, bloc « lecteur actif + POOL ») : `wcA` (actif) + `wcPool` = jusqu'à **8 décodeurs pré-calés** (4 sur iOS/Android) sur tous les plans des **2 s à venir** (`WC_POOL`, `WC_AHEAD_S`, `wcPrepAhead`). À chaque coupe, le décodeur déjà prêt devient actif ; le décodeur libéré est recyclé sur le plan suivant (pas détruit). Décodeurs en attente : tampon limité à 5 frames (`pl.idle`), actif : 14. Récupération auto (`recover()` → logiciel) si un décodeur est en erreur pendant la lecture. Télémétrie `preview_pool_miss` si ≥ 8 plans activés sans décodeur prêt.
- `cutCache` conservé **uniquement en secours** (décodeur pas encore prêt → image du plan au lieu d'un gel/noir), construit seulement à l'arrêt (`SHORT_PLAN=0.5`), jamais pendant la lecture.
- Test harnais node (`/tmp/pool_test.js`, décodeur simulé, latence configure 120-300 ms) : plans 62 ms/latence 300 ms → **0 tick sans frame**, ~2,4 frames distinctes par plan (= vraie vidéo), 64 plans ; idem 40 ms, 125 ms, 250 ms, 500 ms. Export non touché (`wcExportSeek` inchangé).
- À vérifier par l'utilisateur sur PC (Chrome/Firefox) et iPhone avec son projet à coupes ⅛ de temps.
