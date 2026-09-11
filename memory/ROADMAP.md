# BEATCUT — Priorités

## P0 — Validation utilisateur
- Correction `v13.25-long-video` vérifiée : serveur 6/6 + réessai 2/2, navigateur réel Chrome desktop et Chrome mobile simulé, source 185 s, cuts 100/200/250 ms, scrub et export MP4 réel.
- Faire valider sur les propres fichiers longs de l'utilisateur. Aucun défaut bloquant restant dans les scénarios testés ; ne pas déclarer tous les appareils corrigés sur la seule base de Chrome Linux.

## P1 — Ensuite
- Safari/iPhone physique : lecture source longue, scrub tactile, menu mobile, page Série, export complet avec audio.
- Rotation des clés de services signalées comme exposées lors d'un audit antérieur : action utilisateur requise ; ne pas reproduire les clés dans la documentation.

## P2 — Améliorations suivantes, hors portée de la correction actuelle
- Pré-remplir la recherche de clips gratuits selon le style du questionnaire.
- Choisir manuellement une image de vignette par plan.
- Suivre les vignettes manquantes par navigateur dans l'administration.
- Extraire progressivement le moteur de `studio.html`, avec tests de régression avant refactor.

## Suggestion produit
- Ajouter une estimation du temps de préparation de l'aperçu pour les gros fichiers (l'état de préparation et le bouton de réessai existent désormais).