# BEATCUT — Priorités

## P0 — Validation utilisateur
- Blocage Play/écoute sur envoi long échoué corrigé (`v13.27-upload-recovery`) : reprise4MiB, vraie erreur/action, Play différé annulable, audio autonome, lecture locale explicite. Vérifié sur110Mo avec coupure réseau et reprise,17 tests API et régressions vidéo/paroles.
- Tap paroles + pré-écoute commune (`v13.26-tap-lyrics`) vérifiés : 11 groupes de contrôles frontend, 3 tests serveur, timings réellement capturés sauvegardés/rechargés. Validation sur le morceau de l'utilisateur en attente.
- Correction v13.25 du moteur conservée, mais son garde-fou bloquant l'envoi échoué est remplacé par la récupération v13.27. Vérification utilisateur avec son propre fichier toujours nécessaire.
- Faire valider sur les propres fichiers longs de l'utilisateur. Aucun défaut bloquant restant dans les scénarios testés ; ne pas déclarer tous les appareils corrigés sur la seule base de Chrome Linux.

## P1 — Ensuite
- Safari/iPhone physique : Tap paroles et pré-écoute/latence, lecture source longue, scrub tactile, menu mobile, page Série, export complet avec audio.
- Rotation des clés de services signalées comme exposées lors d'un audit antérieur : action utilisateur requise ; ne pas reproduire les clés dans la documentation.

## P2 — Améliorations suivantes, hors portée de la correction actuelle
- Pré-remplir la recherche de clips gratuits selon le style du questionnaire.
- Choisir manuellement une image de vignette par plan.
- Suivre les vignettes manquantes par navigateur dans l'administration.
- Extraire progressivement le moteur de `studio.html`, avec tests de régression avant refactor.
- Tableau récapitulatif des envois/optimisations avec progression et reprise centralisée (les actions par clip et le panneau de lecture existent).

## Suggestion produit
- Tap paroles : reprendre une prise à partir du mot raté plutôt que recommencer l'extrait entier.
- Ajouter une estimation du temps de préparation de l'aperçu pour les gros fichiers (l'état de préparation et le bouton de réessai existent désormais).