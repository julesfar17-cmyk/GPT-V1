# BEATCUT — Produit et état actuel

## Problème original
« Voici mon site en version html copie le et fais en un vrai site fonctionnel qui a une belle page d'accueil un système pour se désabonner une DA plus pro et propre et faire en sorte qu'il soit fonctionnel sur mobile et sur pc. »

BeatCut transforme un morceau et des vidéos en montages synchronisés sur le beat : cuts, paroles, styles, recadrage, hooks et séries de vidéos. Public : artistes et créateurs de contenus musicaux. Langue de communication utilisateur : **français**.

## Exigences essentielles
- Studio réellement utilisable sur ordinateur et mobile ; images animées sur les cuts rapprochés, pas de remplacement systématique par des images fixes.
- Conservation des médias, plans, paroles et réglages ; sauvegarde serveur avec filet local et restauration fiable.
- Aperçu fluide ; export MP4 avec son et qualité finale préservée.
- Authentification email/JWT et Google existantes, abonnements et quotas, désabonnement, suivi administrateur.
- Design V3 existant à préserver ; aucun nouveau parcours marketing pour une correction technique.

## Architecture
- React + Tailwind/shadcn : pages publiques, compte, projets, administration.
- `/app/frontend/src/pages/Studio.js` : route `/studio`, studio intégré dans une iframe.
- `/app/frontend/public/studio.html` : SPA vanilla, moteur WebCodecs, plans et timeline, export hors-ligne, hooks, série, auto-save.
- `/app/frontend/public/v3-skin.css` : style studio.
- FastAPI `/app/backend/server.py` + MongoDB/Motor + GridFS : médias, projets et sauvegardes, quotas, authentification, APIs et télémétrie.
- FFmpeg existant : normalisation des vidéos, proxys H.264 ≤720p avec images clés toutes les 0,5 s, vignettes serveur, assemblage audio export.
- Intégrations existantes : Google Emergent, Stripe, Resend, Groq/Whisper, Replicate ; Mux optionnel dans le transcodage existant. Aucune nouvelle intégration pour la correction des vidéos longues.
- Variables protégées : `frontend/.env:REACT_APP_BACKEND_URL`, `backend/.env:MONGO_URL,DB_NAME`. L'adresse courante est toujours celle de `.env`, pas celle d'un ancien rapport.

## Données / APIs importantes
- `users`, `user_sessions`, `projects`, `project_backups`, médias GridFS `media.files`, `export_logs` (quotas), `export_telemetry`, `save_failures`.
- `/api/projects`, `/api/media/upload`, `/api/media/{id}`, `/api/media/{id}/status`.
- `/api/media/proxy/{id}`, `/api/media/{id}/thumbs`.
- `/api/telemetry/preview`, `/api/telemetry/export`, `/api/proxy/transcribe`.
- Comptes de test et précautions Stripe LIVE : `/app/memory/test_credentials.md`. Ne jamais effectuer de paiement réel ni d'envoi collectif pendant les tests.

## Correction en cours — 13 septembre 2026 — `v13.28-safe-restore`
Utilisateur : « ça semble fonctionner, mais ce message reste tjrs affiché : SAUVEGARDE DÉSACTIVÉE (CHARGEMENT INCOMPLET) ». Correction approuvée, sans désactiver la protection contre les données manquantes.
- Implémentation en cours de vérification : tracker de restauration par projet (`project-restore.js`), emplacements stables des vidéos manquantes, reprise ciblée et réimport dans le même emplacement, protection des plans/paroles et réactivation automatique quand audio/vidéos attendus sont effectivement récupérés.
- `restoreIncomplete` n'est plus réinitialisé aveuglément après récupération de vidéos quelconques. Un échec de chargement JSON reste bloquant et réessayable ; un upload de remplacement doit être confirmé avant déblocage.
- Source principale `/app/frontend/public/studio.html` : `fetchRemoteMorceau`, `loadRemoteMorceau`, `loadAudio`, `recoverMedia`, `retryMissingClip`, `addClip`, `canPersist`, `persistRemote`. Chargements/sauvegardes tardifs protégés par identité du projet.
- Aucun changement d'API/authentification. Smoke et contrôles de syntaxe réussis ; tests de sauvegarde/réouverture réels à terminer avant conclusion.

## Correctif précédent — 13 septembre 2026 — `v13.27-upload-recovery`
Utilisateur : « lorsque je clique sur “Play” ou sur “Écouter l’extrait”, le message “Préparation de l’aperçu fluide pour cette vidéo longue…” apparaît, puis plus rien ne se passe. Cela fait maintenant plus de 30 minutes que j’essaie de lancer la vidéo sans succès. » Capture : « Non sauvegardée — réessayer ». Accord : « Oui corrige le traitement des vidéos longues stp ».

### Cause et changement de comportement
- Défaut confirmé : le garde-fou v13.25 attendait un proxy même avec `_saveFailed` et sans `mediaId`. Aucun proxy ne pouvait donc démarrer. Il examinait aussi les clips non utilisés et n'avait pas de véritable reprise de l'intention Play.
- L'envoi monolithique des gros fichiers était fragile ; le code HTTP de l'échec utilisateur n'est PAS connu. Ne pas affirmer que Cloudflare/413 était la cause certaine sur son appareil.
- Aperçu optimisé toujours préféré par défaut, mais **plus d'attente sans issue**. Erreur réelle visible, reprise d'envoi / d'aperçu, annulation et lecture locale explicitement choisie avec avertissement de saccades et de sauvegarde non confirmée.
- `longPreviewPending` reste un diagnostic (affichage des erreurs/réessais même pendant la lecture locale). Le blocage réel est calculé par `PreviewReadiness` sur les plans utilisés à partir du point demandé ; les clips inutilisés/passés ne bloquent pas.
- Play en attente est annulable, limité à5min et démarre automatiquement si l'aperçu arrive dans ce délai. Après expiration, lancement manuel explicite. Un changement de projet/extrait, annulation ou arrière-plan empêche une reprise tardive.
- « Écouter l'extrait » lit immédiatement l'audio si la vidéo est indisponible, avec indicateur « Lecture audio uniquement ». Le proxy peut être téléchargé/démuxé pendant cette écoute ; la pompe vidéo n'est pas lancée inutilement.

### Transfert et fichiers
- `/app/frontend/public/media-upload.js` : fichiers ≥4MiB transférés par blocs4MiB, trois tentatives bornées par bloc ; identifiant/fingerprint utilisateur dans localStorage, reprise sans renvoi des blocs déjà reçus. Pas de service externe ajouté.
- `/app/backend/resumable_media.py` : sessions propriétaires MongoDB + fragments temporaires, validations taille/index/hash/quotas, finalisation sous verrou temporaire vers `_store_media_file` existant ; déduplication conservée, sessions et parties avec TTL24h. Réponses Pydantic sans BSON exposé.
- Nouvelles routes authentifiées : `POST /api/media/uploads` (UUID, filename, content_type, size), `GET /api/media/uploads/{uuid}`, `PUT /api/media/uploads/{uuid}/chunks/{index}` (corps brut), `POST .../complete`, `DELETE .../{uuid}`.
- Maximum inchangé : **300 000 000 octets par fichier** ; message backend corrigé (ancien texte80Mo). Au-delà, erreur claire, pas de fausse préparation ; lecture locale seulement si le navigateur sait décoder la source.
- `API.uploadMedia` peut rendre l'identifiant immédiatement après stockage pour les clips, sans bloquer sur le transcodage ; états d'envoi, transcodage et proxy distingués. `_sourceFile` conservé pour la reprise, flags d'erreur nettoyés au succès, clips retirés ignorés par les callbacks.
- Polling proxy limité par une vraie échéance10min, requêtes et téléchargements avec délais ; expiration visible et réessai possible. Le garde-fou ne remplace jamais les cuts par des images fixes.
- Moteur vidéo/WebCodecs, export sur source originale, paroles/coupes/recadrages du projet utilisateur non modifiés.

### Vérification finale
- **9/9** tests API des transferts reprenables : ordre libre, doublon identique, conflit, blocs manquants/invalides, taille max, expiration/TTL, authentification/isolation propriétaire, finalisation concurrente/idempotente et intégrité du téléchargement.
- Envoi réel **110 000 000 octets**, vidéo H.264185s avec B-frames/GOP10s : trois coupures réseau injectées uniquement dans le test sur le bloc1, reprise sur le même UUID, bloc0 envoyé une seule fois, aucun envoi monolithique, hash final identique. Proxy réel obtenu.
- Vérification complémentaire avec **vrais téléchargements/décodage de proxy** : Play se relance, proxy termine pendant écoute audio, annulation/changement d'extrait empêchent l'autoplay, clips inutilisés/passés ignorés ; lecture locale montre des frames animées et garde un réessai visible.
- Cuts100/200/250ms : 452 ticks / zéro frame manquante ou erronée sur l'aperçu optimisé. Export MP4 réel1,2s/36images avec audio, source originale conservée. **8/8** régressions API proxy passent. **11 groupes Tap paroles** repassés sans erreur.
- UI sans débordement à320/768/1024/1440, actions ≥44px ; syntaxe Python/JS et contrôle `no-undef` réussis.
- Rapports : `test_reports/iteration_38.json`, `frontend_long_preview_iter38.json`, `frontend_preview_final_iter39.json`, `iteration_39.json`, `pytest/iter38_resumable_uploads.xml`, `pytest/iter39_proxy_regression.xml`.
- Aucun mock dans l'application. **TEST-ONLY FAULT INJECTION (MOCKED)** : interruption de requêtes de blocs dans le test ; requêtes normales, stockage, médias, décodeurs et exports réels. Les scénarios d'état isolés d'iteration38 sont complétés par les vrais téléchargements d'iteration39.
- Fixtures persistantes : `/root/beatcut-test-assets/` (générateur `/app/frontend/tests/generate_long_gop_assets.py`), rapports/logs dans `/app/test_reports/`. Des médias QA restent sur le compte démo pour les régressions ; aucun projet utilisateur existant modifié, aucun compte créé ni credential changé.
- Limites : vidéo locale originale peut saccader sur cuts rapides ; Safari/iPhone physique, HEVC/4K et fichier exact de l'utilisateur non validés dans ce passage.

## Fonction précédente — 13 septembre 2026 — Tap paroles
Utilisateur : « On vas ajouter une fonctionnalité similaire à tap for cut. Ce seras une fonction qui permettra de caler ses paroles en appuyant sur l’écran avec la même possibilité de ralentir l’extrait pour être plus précis. Aussi sur le compte à rebours avant que ça commence joue la musique juste avant la l’extrait (à volume réduit) pour ce soit plus facile d’attaquer. »
Choix confirmé : « Oui mot par mot ! » ; vitesses 100/75/50 %, préparation musicale aussi sur Tap for cut, recommencer et valider avant remplacement.

### Implémenté — `v13.26-tap-lyrics`
- **Tap paroles** dans le panneau Paroles et Plus sur mobile : paroles existantes de l'extrait préremplies, ou collage/édition directe sans transcription ni appel IA.
- Un appui tactile, clic, Entrée sur la zone ou Espace cale le mot suivant sur le temps source. Pas de quantification au beat ; compteur, mot à venir et contexte visibles, ralenti 100/75/50 %.
- Prise isolée de `M.words` jusqu'à validation ; prise incomplète non applicable, réessai, réécoute à vitesse normale avec surlignage ; Annuler conserve le projet.
- Application : temps absolus dans l'extrait, fins positives et `hardEnd`, mots hors extrait conservés, métadonnées des mots identiques conservées ; historique Undo existant, sauvegarde serveur normale. Protection si le projet/extrait/paroles change pendant une prise.
- **Pré-écoute commune** Tap paroles/Tap for cut : 3 secondes de décompte, passage précédent à gain 0,25, même vitesse de lecture, rampe 20 ms vers gain 1 au départ. Une seule source audio traverse la jonction, horloge WebAudio et compensation de latence ; si l'extrait commence au début du morceau, la partie antérieure inexistante reste silencieuse.
- Annulation arrête source, gain, callbacks et animations ; fermeture lors de navigation/arrière-plan, protection contre touches maintenues/doubles événements.
- Modules : `/app/frontend/public/tap-audio.js` (horloge/pré-écoute), `tap-lyrics.js` (prise/relecture/validation), `tap-lyrics.css` (UI V3 responsive). Chargés par `studio.html` ; moteur vidéo/proxy et export inchangés.
- Adaptateur explicite `window.BeatCutTapHost` défini dans `studio.html` : getters sur l'état courant (`M`, buffer, extrait, contexte audio) et actions de validation/rafraîchissement. Les modules n'accèdent pas à des variables globales lexicales implicites ; contrôle `no-undef` réussi sur les deux fichiers JS.
- Paroles affichées sans traduction automatique ni capitalisation forcée ; nouveau modal gère lui-même FR/EN, attribut `translate="no"` respecté par le traducteur local existant.
- Aucun nouveau service externe, aucun changement d'authentification/prix/quotas et aucune API simulée dans l'application.

### Tests de cette fonctionnalité
- Smoke réel `/studio` iframe : 75 %, premier mot calé, annulation sans erreur.
- Serveur : 3/3 tests de création/lecture/mise à jour/suppression de projets jetables, préservation des timings/`hardEnd`/métadonnées (`test_iter36_taplyrics_persistence.py`). Aucun projet utilisateur existant modifié.
- Base frontend validée : ouverture desktop et mobile, préremplissage, texte vide, Unicode, pointer+Space, prise incomplète, application/métadonnées/Undo, annulation Tap for cut, aucun débordement à320/768/1024/1440.
- Mesures audio réelles avec AnalyserNode à100/75/50 : amplitude multipliée par ~4 au départ, offset pré-écoute exact, continuité mathématique sans écart, bornes début0/0,5s correctes.
- Le premier harnais signalait à tort l'entrée mobile : le tutoriel d'accueil était encore ouvert et le test cliquait derrière. Harnais corrigé pour passer le tutoriel normalement et ouvrir le panneau mobile via ses boutons. Aucune modification du tutoriel dans le produit.
- **Extension finale réussie** : temps source à100/75/50 %, réécoute à100 % et arrêt, toucher via API tactile Chrome, fin naturelle, conflit de brouillon refusé, annulation sans reprise différée, Tap for cut ralenti/quantification/touche maintenue, sauvegarde serveur du calage réellement appliqué et métadonnées exactes. Aucun runtime error. Résultats : `/app/test_reports/frontend_taplyrics_iter36.json`, synthèse `/app/test_reports/iteration_37.json`.
- Mesures capture : ~0,75 s réelles donnent respectivement ~0,749 / 0,562 / 0,374 s source. Décompte et changement de volume indépendants des timers visuels. Texte utilisateur préservé en interface anglaise, casse incluse.
- Tests de syntaxe JS réussis. Validation physique Safari/iPhone et latence d'un casque Bluetooth non effectuées ; Chrome tactile/viewport mobile n'est pas Safari iOS.
- Redo n'existe pas dans le studio et n'a pas été ajouté : hors demande utilisateur. Undo existant utilisé.

## Correction précédente — 11 septembre 2026
Utilisateur : « J'ai limpression qu'il y a parfois des bugs quand le vidéo importée est longue genre 2 OU 3 ;inutes ou pluis ».
Plan approuvé (« bien ») : reproduire avec sources ≥2–3 minutes, corriger le lecteur et vérifier les coupes rapprochées ; Safari/iPhone ensuite.

### Implémenté — build `v13.25-long-video`
- Imports locaux : chargement du proxy d'aperçu après upload/optimisation, auparavant absent du chemin `startClipUpload`. Le chargement et l'activation du proxy attendent la fin d'une lecture ou d'un export ; téléchargement HTTP validé.
- Démarrage sûr : pour les sources ≥90 s, la lecture attend le proxy (`longPreviewPending`) plutôt que de jouer une source à GOP long avec des images manquantes. État visible par clip ; réessai explicite en cas d'échec (`?retry=true`, réinitialisation du flag d'échec serveur seulement à la demande). Export inchangé et non bloqué par ce garde-fou d'aperçu.
- Serveur : politique proxy v2. Les vidéos ≥90 s passent par le proxy à GOP court même en H.264 ≤720p. Anciennes décisions « proxy inutile » réévaluées paresseusement à la prochaine demande, sans migration de masse. Les courtes vidéos déjà légères conservent le chemin rapide.
- Lecteur : index binaire des keyframes sans modifier l'ordre des échantillons/B-frames ; budget qui compte les sorties asynchrones en attente, purge des frames consommées, flush unique en fin de flux, dernière image accessible et repli logiciel conservé après seek.
- Pool inchangé (8 desktop/4 mobile), sans retour aux plans courts volontairement figés. Préchargement amorcé avant le son, horizon avancé pendant les plans longs, préparation annulable ; pompe de décodage commune à lecture, boucle et série.
- Scrub : une seule relance d'aperçu, attente d'une frame à jour même en petite avance après une pause.
- L'export reste sur `clip.wc` original ; l'aperçu préfère `clip.wcProxy`.

### Vérification
- Base avant correction : vrai fichier H.264 185 s, 4440 images, GOP 10 s, B-frames ; absence de proxy sur long720 et dépassement du tampon reproduits (`iteration_32.json`).
- Serveur après correction : 6/6 tests réels passent (`iteration_33.json`, `test_long_proxy_policy2_iter33.py`). Proxy long720, réutilisation, ancien média, long>720, court720 et refus non authentifié ; durée et GOP vérifiés avec FFmpeg.
- Régression serveur finale : 6/6 HTTP/médias + 2/2 tests unitaires de réessai explicite (stockage simulé dans ces deux tests uniquement, jamais dans l'application) ; XML `iter35_long_proxy_final.xml` et `iter35_proxy_retry.xml`.
- Les premiers harnais frontend contenaient des erreurs : timecode source utilisé comme timecode montage, puis accès `window.clips` au lieu de la variable lexicale `clips`. Ces résultats ne prouvent PAS un défaut d'import ou de scrub. Aucun contournement QA ajouté à l'application.
- Harnais corrigé : `/app/frontend/tests/test_long_preview_regression_iter34.py`, vrai `/studio`/iframe, projet navigateur non enregistré, médias et décodeurs réels, transport/audio réel, export MP4 vers un sink sans décompte. Résultat final à consulter dans `/app/test_reports/frontend_long_preview_regression_iter34.json`.
- Mesure diagnostique importante : l'original 185 s / GOP10 s forcé en lecture peut encore manquer des frames sur les cuts 100 ms ; le proxy GOP0,5 s donne zéro frame manquante. **Ne pas supprimer l'attente du proxy pour les vidéos longues.** L'export décode l'original hors temps réel, donc garde la résolution finale.
- **Vérification finale réussie** (`iteration_35.json` + données `frontend_long_preview_regression_iter34.json`) : import réel dans l'iframe, attente de proxy et bouton de réessai, 5 seeks/scrubs exacts et pixels différents, lecture réelle avec audio et coupes 100/200/250 ms sur source 185 s. Proxy desktop : 690 ticks / 0 frame manquante / 0 mauvaise frame ; Chrome mobile simulé : 595 ticks / 0 manquante / 0 mauvaise. Pool 8/4, annulation, boucle, budgets mémoire et récupération logiciel vérifiés.
- Export MP4 réel réussi via `exportOffline` (source originale, assemblage audio serveur réel) : 1,2 s / 36 images / 1920×1080 / 1 606 498 octets ; pas de téléchargement décompté, aucun paiement/email. Aucun service simulé dans l'application.
- Validation sur les propres fichiers de l'utilisateur en attente. Les tests portent sur H.264 720p 185 s / GOP10 s avec B-frames, pas sur toutes les résolutions/codecs/appareils.
- Firefox non installé dans le conteneur ; Safari/iPhone physique non disponible. Émulation mobile Chrome ≠ validation iPhone.

## Documentation
- Historique complet antérieur préservé dans `/app/memory/CHANGELOG.md` (ancien PRD >1000 lignes, contient des décisions historiques remplacées depuis).
- Priorités actuelles : `/app/memory/ROADMAP.md` ; elles priment sur les anciens backlogs du changelog.
## 2026-06 — Correctif layout timeline PC (scroll vertical parasite)
- Cause : `tap-lyrics.css` définissait `.tl-body` (et autres `.tl-*`) sans scope ; la règle `width:min(100%,660px);margin:auto;padding:28px 24px` s'appliquait aussi au `.tl-body` de la timeline du studio → timeline réduite à 660 px, centrée, décalée vers le bas et débordant de la page.
- Fix : toutes les règles de `tap-lyrics.css` sont maintenant préfixées `#tapLyricsOverlay` ; `grid-template-columns:minmax(0,1fr)` ajouté pour ne pas hériter du `64px 1fr` du studio.
- Bonus : la ligne timeline desktop (`v3-skin.css`) passait de 185 px à 199 px = 40 (barre) + 26 (bande scrub) + 40 (paroles) + 92 (plans) + 1 (bordure) ; 14 px de débordement existaient depuis l'ajout de la bande de scrub.
- Vérifié par captures : desktop 1920×800 → scrollHeight = innerHeight = 800, timeline pleine largeur ; mobile 390×844 → aucun scroll ; overlay Tap paroles rendu correctement.
- Règle : ne jamais utiliser le préfixe `.tl-` hors de `#tapLyricsOverlay` (collision avec la timeline `.tl-*`).

## 2026-06 — Firefox : gels de l'aperçu (avec ou sans cuts) — build v13.29-ff-diag
- Firefox 151 installé dans le conteneur (`playwright install firefox` + `apt install libavcodec59` pour le H.264 ; AudioContext reste `suspended` en headless → le harnais `frontend/tests/ff_freeze_probe.py` simule l'horloge audio). Firefox Linux (ffmpeg) lit sans gel ; le WMF Windows du user n'est pas reproductible ici.
- Cause la plus probable identifiée (démontrée par injection de latence dans Chrome) : le budget `pending` de `SegPlayer.fill()` (v13.25) bloque l'alimentation dès que `frames+pending ≥ 16`. Un décodeur à forte latence interne (WMF Windows garde 16+ images avant la 1re sortie) → plus rien envoyé, plus rien reçu = gel définitif, cuts ou pas. Ancien code avec latence 20 simulée : `aBuf 0 / aPend 18`, gels à chaque plan ; nouveau code : 0 gel.
- Fix : apprentissage de la latence (`latencyExtra` +4 par 400 ms de silence total, max 24, partagé via `SegPlayer.learnedExtra`), insertion triée des frames (ordre de décodage toléré), anti-blocage si le tampon est plein d'images toutes « en avance » (> 300 ms, lecture seule), `lastOutTs` remis à zéro au seek.
- Diagnostic : `decoder_ts_anomaly`, `decoder_latency_bump`, `preview_stall` enrichi (pending, si, target, buf0/bufN, curTs, ooo, mism, stuckN, pool, fps, err) ; jusqu'à 6 stalls par session ; clés ajoutées dans `_PREVIEW_EVENT_KEYS` côté serveur. Lire : `db.preview_logs` filtré sur `ctx.ua` Firefox/Windows.
- Régression : `ff_freeze_probe.py` Chrome + Firefox (0 gel, 0 anomalie), fautes `order`/`shift`/`latency` (lecture continue), `test_preview_final_iter39.py` PASS (proxy réel 185 s, cuts rapides 0 manquante, export MP4 OK).
- À faire : le user doit tester sur la PREVIEW avec Firefox Windows (télémétrie lisible ici), puis redéployer.

## 2026-06 — Remplacer le clip = tous les plans + polish mobile (sans changer l'interface)
- `psReplace()` (feuille « Ce plan », mobile) : affiche désormais TOUS les plans disponibles (une rangée horizontale par clip, vignette + durée « 2.3s », nom du clip si plusieurs clips, plan courant surligné et centré). Tap → `sheetPlan.clip/seek`, verrouillé. Testids `plan-replace-clip-{ci}-{si}`. i18n ajouté (hint, toast).
- Header mobile : spacer masqué, gap 5 px, HOOK padding 12, export padding 11 → « EXPORTER LA VIDÉO » ne déborde plus à 390 px et le titre affiche « Recette 1… » (ellipsis) au lieu d'une lettre. Undo : glyphe 22 px centré, disabled opacity .35.
- Feuille plan : hint `#psClips .hint` plus lisible (texte 80 %). Carte morceau mobile : `.v3-del` 32×32 rond (le `button{min-height:44px}` mobile l'étirait en rectangle), badge « prêt » réaligné. Glyphe « ↶ » du menu Plus agrandi.
- Cache : `v3-skin.css?v=13.29`, `tap-lyrics.css?v=13.29` (l'ancien `?v=13.19` aurait gardé l'ancien CSS chez le user après déploiement).
- Harnais : `frontend/tests/mobile_walk.py` (captures iPhone 390×844 FR de toutes les feuilles) ; vérifié desktop 1920 sans scroll.

## 2026-06 — « Preview OK, prod rebug » : investigation Firefox/gels (build v13.30-stall-diag)
- Prod (beat-cut.com) sert bien v13.29 (cache-control no-store). Télémétrie prod (admin, 3 j) : 283 sessions, 44 % avec `preview_stall`, 170 `decoder_error`, 9 `decoder_latency_bump` (le correctif latence se déclenche réellement en prod), 1 `decoder_ts_anomaly`. Stalls sur TOUS les navigateurs (Chrome 73/135, Safari macOS 14/30, Firefox 4/6) → pas spécifique Firefox.
- Vidéos réelles du user récupérées depuis prod (compte admin = son compte) dans `/app/memory/prodmedia/` (TADC 1080p60 H.264 High + PNG attaché, proxy 720p60 ; Spiderman 720x1280 30 fps sans proxy). Rejouées sur la preview via `frontend/tests/prod_media_probe.py` (upload réel → proxy → 52 cuts) : Chrome ET Firefox Linux = 0 gel, 60 fps. Le code + les fichiers sont sains ; la différence est l'environnement du user (Firefox Windows/WMF, GPU) ou le serveur prod.
- Ajouts : `GET /api/admin/telemetry/preview/raw?browser=Firefox&hours=48&limit=30&types=preview_stall,...` (lots bruts, admin) ; `preview_stall` enrichi (durS, lastTs, seek, pStart/pEnd, tNow) ; `wcIndexSamples` corrige `durationS` d'après les échantillons (piste fMP4/edit-list erronée → boucle `tt%=d` à vide = gel) + event `duration_fixed`.
- Étape suivante : le user déploie, reproduit 1 min sur prod avec Firefox, puis lire `curl -b /app/memory/.prod_cookies 'https://beat-cut.com/api/admin/telemetry/preview/raw?browser=Firefox&hours=6'` (cookie admin prod dans `/app/memory/.prod_cookies`, 7 j).
- Env : Firefox Playwright désormais dans `/app/.pw-browsers` (PLAYWRIGHT_BROWSERS_PATH) ; après redémarrage du pod, refaire `apt-get install -y libavcodec59` (H.264 Firefox).
