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

## Dernière demande approuvée — 13 septembre 2026
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