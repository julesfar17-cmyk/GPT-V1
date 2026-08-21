import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const TOC = [
  ["pages", "Les pages du site"],
  ["etapes", "Créer une vidéo en 4 étapes"],
  ["studio-pc", "Le studio sur ordinateur"],
  ["clips", "Panneau Clips"],
  ["son", "Panneau Son"],
  ["paroles", "Panneau Paroles"],
  ["style", "Panneau Style"],
  ["timeline", "La timeline"],
  ["mobile", "Le studio sur mobile"],
  ["serie", "Série de vidéos"],
  ["export", "Exporter sa vidéo"],
  ["raccourcis", "Raccourcis clavier"],
];

function Section({ id, title, intro, children }) {
  return (
    <section id={id} className="scroll-mt-20 bg-card border border-border p-6 sm:p-8 mb-6" data-testid={`aide-section-${id}`}>
      <h2 className="font-display text-xl font-bold mb-2">{title}</h2>
      {intro && <p className="text-sm text-muted-foreground mb-5 max-w-3xl leading-relaxed">{intro}</p>}
      {children}
    </section>
  );
}

function Item({ name, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 py-2.5 border-b border-border/50 last:border-0">
      <span className="font-osd text-[11px] tracking-[0.12em] uppercase text-primary shrink-0 sm:w-56">{name}</span>
      <span className="text-sm text-muted-foreground leading-relaxed">{children}</span>
    </div>
  );
}

export default function Aide() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar />
      <main className="flex-1 mx-auto w-full max-w-5xl px-5 sm:px-8 py-12">
        <p className="font-osd text-xs tracking-[0.25em] text-primary mb-3">[ AIDE ]</p>
        <h1 className="font-display text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
          Tout comprendre de BeatCut.
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl mb-8 leading-relaxed">
          BeatCut transforme ton morceau en vidéos calées sur le beat, prêtes pour TikTok, Reels et Shorts.
          Cette page explique chaque page du site et chaque bouton du studio, sur ordinateur comme sur téléphone.
        </p>

        <nav className="flex flex-wrap gap-2 mb-10" data-testid="aide-toc">
          {TOC.map(([id, label]) => (
            <a key={id} href={`#${id}`}
              className="border border-border px-3 py-1.5 text-[11px] font-osd tracking-wider uppercase text-muted-foreground hover:border-foreground hover:text-foreground transition-colors">
              {label}
            </a>
          ))}
        </nav>

        <Section id="pages" title="Les pages du site"
          intro="Le site se compose de quelques pages simples. Voici à quoi sert chacune.">
          <Item name="Accueil">La vitrine de BeatCut : présentation, exemples, tarifs et bouton pour commencer. C'est la page sur laquelle tu arrives en visitant beat-cut.com.</Item>
          <Item name="Créer un compte / Connexion">Inscription en 30 secondes avec Google ou par email + mot de passe. Tu y coches les CGV et, si tu veux, la newsletter. Un lien « Mot de passe oublié ? » permet de recevoir un email de réinitialisation.</Item>
          <Item name="Le Studio">Le cœur de BeatCut : c'est là que tu déposes ton morceau, ajoutes tes clips, cales tes paroles et exportes ta vidéo. Tout est expliqué en détail plus bas.</Item>
          <Item name="Mes morceaux">Dans le studio, l'onglet « Morceaux » liste tous tes projets. Chaque morceau garde son montage, ses paroles et son style. Le bouton « Nouveau morceau » crée un projet vierge, et le guide « Bien démarrer » te rappelle les 4 étapes.</Item>
          <Item name="Série de vidéos">Toujours dans le studio : génère plusieurs variantes d'une même vidéo d'un coup, pour poster tous les jours sans refaire le montage.</Item>
          <Item name="Mon compte">Ton tableau de bord : abonnement (activer, gérer, annuler en 2 clics), jauge de stockage utilisé, code de parrainage, et suppression définitive du compte si tu le souhaites.</Item>
          <Item name="Contact">Une question, un bug, une idée ? Écris-nous à contact@beat-cut.com — on répond vite.</Item>
          <Item name="CGV / Confidentialité / Mentions légales">Les pages légales : conditions de vente, gestion de tes données et informations sur l'éditeur du site.</Item>
        </Section>

        <Section id="etapes" title="Créer une vidéo en 4 étapes"
          intro="Peu importe ton niveau, le studio suit toujours la même logique :">
          <Item name="1 — Dépose ton morceau">Glisse ton fichier audio (MP3, WAV...). BeatCut détecte automatiquement le tempo et les temps forts.</Item>
          <Item name="2 — Ajoute tes clips">Importe tes propres vidéos ou pioche dans la banque de clips libres de droits. Elles sont découpées en plans et placées sur le beat automatiquement.</Item>
          <Item name="3 — Paroles et style">Ajoute tes paroles (détection auto ou collage manuel), puis choisis la police, les couleurs, les effets et les animations.</Item>
          <Item name="4 — Exporte">Clique sur « Exporter la vidéo » : le fichier MP4 vertical est généré directement dans ton navigateur, prêt à poster.</Item>
        </Section>

        <Section id="studio-pc" title="Le studio sur ordinateur — la barre du haut"
          intro="Sur PC, une barre d'outils en haut de l'écran donne accès à tout. De gauche à droite :">
          <Item name="Logo BEATCUT">Clic = retour à l'accueil du studio (liste de tes morceaux).</Item>
          <Item name="Clips">Ouvre le panneau d'import des vidéos (voir « Panneau Clips » plus bas).</Item>
          <Item name="Enregistré">Indicateur de sauvegarde : ton projet est enregistré automatiquement à chaque modification. Tu ne peux rien perdre.</Item>
          <Item name="Thème">Bascule l'interface entre sombre et clair.</Item>
          <Item name="Annuler">Annule la dernière action (équivalent Ctrl+Z). Utilisable plusieurs fois d'affilée.</Item>
          <Item name="Versions">Historique des versions du morceau : BeatCut garde des sauvegardes régulières, tu peux revenir à un état précédent du montage à tout moment.</Item>
          <Item name="Série">Ouvre le mode « Série de vidéos » pour générer plusieurs variantes d'un coup.</Item>
          <Item name="Style">Ouvre le panneau Paroles &amp; style (texte, effets, animations).</Item>
          <Item name="Exporter la vidéo">Le bouton rouge : lance le rendu final de ta vidéo en MP4.</Item>
        </Section>

        <Section id="clips" title="Panneau Clips"
          intro="C'est ici que tu gères les images de ta vidéo. Tes vidéos sont découpées en plans et placées sur le beat automatiquement.">
          <Item name="Importer des vidéos">Glisse tes fichiers ou clique pour les sélectionner. Tu peux en importer plusieurs à la fois.</Item>
          <Item name="Plans par vidéo">« Auto » laisse BeatCut décider combien de plans extraire de chaque vidéo. Tu peux aussi fixer un nombre précis.</Item>
          <Item name="Banque de clips">Des milliers de vidéos libres de droits, cherchables par mot-clé (voiture, ville, nuit...). Pratique si tu n'as pas tes propres images.</Item>
          <Item name="Récupérer mes vidéos déjà envoyées">Réutilise les vidéos que tu as importées dans tes autres morceaux, sans les renvoyer.</Item>
          <Item name="Plein écran">Affiche l'aperçu vidéo en grand (touche F sur PC).</Item>
        </Section>

        <Section id="son" title="Panneau Son — ton extrait"
          intro="Ta vidéo ne dure que quelques secondes : ce panneau sert à choisir LE bon extrait de ton morceau.">
          <Item name="Dépose ton morceau">Importe ton fichier audio. Le tempo et les beats sont détectés automatiquement.</Item>
          <Item name="Libre / Trouver le drop">« Trouver le drop » repère automatiquement le moment le plus fort du morceau. « Libre » te laisse choisir le point de départ à la main.</Item>
          <Item name="Début">Le point de départ exact de ton extrait dans le morceau.</Item>
          <Item name="Durée (boucle parfaite)">BeatCut propose une durée qui tombe pile sur un nombre entier de mesures : la vidéo boucle parfaitement quand elle est rejouée.</Item>
          <Item name="Tempo / TAP">Si le tempo détecté est faux, corrige-le à la main ou tape le bouton TAP en rythme avec le morceau.</Item>
        </Section>

        <Section id="paroles" title="Panneau Paroles"
          intro="Les paroles s'affichent mot à mot, synchronisées avec la voix.">
          <Item name="Détecter les paroles">BeatCut écoute ton extrait et écrit les paroles automatiquement, avec le bon timing pour chaque mot.</Item>
          <Item name="J'ai mes paroles">Tu colles ton texte, et BeatCut le cale sur la voix. Plus fiable si ta diction est rapide ou ton texte particulier.</Item>
          <Item name="Caler mes paroles">Mode manuel : tape en rythme pour poser chaque mot exactement où tu veux.</Item>
          <Item name="Recaler les paroles">Relance la synchronisation si le calage a glissé après une modification.</Item>
          <Item name="Repartir de zéro">Efface les paroles actuelles pour recommencer proprement.</Item>
        </Section>

        <Section id="style" title="Panneau Style"
          intro="Quatre onglets : Styles, Texte, Effets, Animation. C'est ici que ta vidéo prend sa personnalité.">
          <Item name="Styles">Des presets complets prêts à l'emploi. Un clic applique police + couleurs + effets d'un coup. « Enregistrer comme mon style » sauvegarde ton réglage actuel pour le réutiliser sur tes prochains morceaux.</Item>
          <Item name="Texte — Police">18 polices : impact massif (Anton, Archivo Black), manuscrit (Caveat, Marker), rétro (VT323, Silkscreen), néon (Monoton), gothique (Fraktur), glitché (Rubik Glitch)...</Item>
          <Item name="Texte — Affichage">« Mot seul » : un mot à la fois, style TikTok. « Phrase » : la ligne complète. « Étalé » : les mots se répartissent sur l'écran.</Item>
          <Item name="Texte — Réglages">Taille (jusqu'à MAX), épaisseur (fin / normal / gras), casse (MAJUSCULES), couleur, position (haut / centre / bas), espacement des lettres et inclinaison.</Item>
          <Item name="Karaoké">« Mot en cours coloré » : le mot chanté prend une couleur différente, comme un karaoké.</Item>
          <Item name="Contour / Lueur / Ombre">Contour noir ou blanc autour du texte, lueur néon (douce ou forte), ombre portée : tout pour que le texte reste lisible sur n'importe quelle image.</Item>
          <Item name="Lignes CRT / Fond">« Lignes d'écran rétro » ajoute un effet vieil écran sur le texte. « Fond derrière le texte » pose un bandeau de couleur pour un look sous-titre.</Item>
          <Item name="Mots mis en avant">Clique sur un mot de tes paroles pour lui donner sa propre taille, sa propre couleur, voire sa propre police. Parfait pour faire ressortir les punchlines.</Item>
          <Item name="Effets vidéo">Appliqués au rythme des coupures : Flash blanc, Zoom punch, Secousse, Glitch, VHS, Grain, Saturé 4K, Glow, Caméra instable, Fisheye.</Item>
          <Item name="Animation des mots">Comment chaque mot apparaît : Aucune, Pop, Fondu, Glissé, Zoom ou Secousse — avec un aperçu animé de chaque option. Une case permet de garder le mot affiché jusqu'au suivant.</Item>
        </Section>

        <Section id="timeline" title="La timeline (bas de l'écran sur PC)"
          intro="La timeline montre tes plans vidéo et tes paroles dans le temps. Deux onglets : « Plans » et « Paroles ».">
          <Item name="Couper ici">Coupe le plan à l'endroit de la tête de lecture, pour le diviser en deux.</Item>
          <Item name="Beat : ON / OFF">Quand c'est ON, toutes les coupes se calent automatiquement sur les temps forts du morceau. C'est le cœur de BeatCut.</Item>
          <Item name="Mélanger">Redistribue aléatoirement l'ordre des plans, pour tester une autre version du montage en un clic.</Item>
          <Item name="Sans coupes">Désactive le découpage : la vidéo joue tes clips en continu, sans coupes sur le beat.</Item>
          <Item name="Verrouiller">Verrouille le plan sous la tête de lecture : il ne bougera plus quand tu mélanges ou modifies le reste.</Item>
          <Item name="Supprimer / Coller au curseur">Supprime le plan sélectionné, ou colle un plan copié à la position du curseur.</Item>
          <Item name="Zoomer / Dézoomer / Adapter">Zoom avant et arrière sur la timeline. « Adapter » (ou « Tout voir ») recadre pour afficher tout l'extrait d'un coup.</Item>
          <Item name="Clic sur un plan">Sélectionne le plan : tu peux alors le remplacer, changer le moment exact du clip utilisé, le découper ou le supprimer.</Item>
        </Section>

        <Section id="mobile" title="Le studio sur mobile"
          intro="Sur téléphone, le studio adopte une interface façon CapCut : aperçu en haut, timeline au milieu, barre d'outils en bas.">
          <Item name="Barre du bas — Clips">Importer tes vidéos, ouvrir la banque de clips libres de droits, régler les plans par vidéo.</Item>
          <Item name="Barre du bas — Son">Déposer ton morceau, choisir le début de l'extrait, trouver le drop, régler le tempo.</Item>
          <Item name="Barre du bas — Paroles">Détection automatique, collage de ton texte ou calage manuel des paroles.</Item>
          <Item name="Barre du bas — Style">Polices, couleurs, effets vidéo et animations des mots.</Item>
          <Item name="Barre du bas — Plus">Le menu réglages : Annuler la dernière action, Versions du morceau, Revoir le tutoriel, changer de langue (Français / English), Retour à l'accueil et Mon compte.</Item>
          <Item name="Toucher un plan">Ouvre la feuille « Ce plan » avec 5 actions : Remplacer le clip, Autre plan (changer le moment du clip utilisé), Découper en 2, Supprimer, et Verrouiller ce plan.</Item>
          <Item name="Menu (3 barres)">En haut : navigue entre Accueil, Morceaux, Série et Compte.</Item>
        </Section>

        <Section id="serie" title="Série de vidéos"
          intro="Pour poster tous les jours sans refaire le montage : génère plusieurs variantes d'une même vidéo.">
          <Item name="Morceau">Choisis le projet qui sert de base à la série.</Item>
          <Item name="Nombre de vidéos">Combien de variantes générer (montages différents, mêmes paroles et même style).</Item>
          <Item name="Préparer les vidéos">Lance la génération des variantes. Chacune a un ordre de plans différent.</Item>
          <Item name="Choisir les meilleures">Regarde chaque variante et coche celles que tu veux garder.</Item>
          <Item name="Exporter la sélection">Exporte toutes les vidéos cochées d'un coup.</Item>
        </Section>

        <Section id="export" title="Exporter sa vidéo"
          intro="L'export se fait directement dans ton navigateur : rien n'est envoyé sur un serveur pour le rendu.">
          <Item name="Exporter la vidéo">Le bouton rouge en haut à droite (PC) lance le rendu. Une barre de progression s'affiche, puis le fichier MP4 se télécharge.</Item>
          <Item name="Format">Vidéo verticale 9:16, optimisée pour TikTok, Reels et Shorts. Le format est réglable via le bouton « Format de la vidéo » près de l'aperçu.</Item>
          <Item name="Filigrane">Sur le plan gratuit, un filigrane BeatCut est ajouté à l'export. Il disparaît avec un abonnement (7 jours d'essai offerts sur le plan Pro).</Item>
          <Item name="Exports restants">Ton compteur d'exports du mois est visible dans la barre du studio. Il se remet à zéro chaque mois selon ton plan.</Item>
        </Section>

        <Section id="raccourcis" title="Raccourcis clavier (PC)">
          <Item name="Espace">Lecture / pause de l'aperçu.</Item>
          <Item name="Ctrl + Z">Annuler la dernière action.</Item>
          <Item name="F">Aperçu en plein écran.</Item>
        </Section>

        <div className="bg-card border border-primary p-6 sm:p-8 text-center">
          <p className="font-display text-lg font-bold mb-2">Encore une question ?</p>
          <p className="text-sm text-muted-foreground mb-4">On répond à tous les emails, souvent le jour même.</p>
          <a href="mailto:contact@beat-cut.com" data-testid="aide-contact-button"
            className="inline-block bg-primary text-white font-bold px-6 py-3 hover:opacity-90 transition-opacity">
            Écrire à contact@beat-cut.com
          </a>
        </div>
      </main>
      <Footer />
    </div>
  );
}
