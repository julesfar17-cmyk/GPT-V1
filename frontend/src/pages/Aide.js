import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { useI18n } from "@/i18n";

const CONTENT = {
  fr: {
    eyebrow: "[ AIDE ]",
    title: "Tout comprendre de BeatCut.",
    lead: "BeatCut transforme ton morceau en vidéos calées sur le beat, prêtes pour TikTok, Reels et Shorts. Cette page explique chaque page du site et chaque bouton du studio, sur ordinateur comme sur téléphone.",
    contactTitle: "Encore une question ?",
    contactText: "On répond à tous les emails, souvent le jour même.",
    contactBtn: "Écrire à contact@beat-cut.com",
    sections: [
      {
        id: "pages", title: "Les pages du site",
        intro: "Le site se compose de quelques pages simples. Voici à quoi sert chacune.",
        items: [
          ["Accueil", "La vitrine de BeatCut : présentation, exemples, tarifs et bouton pour commencer. C'est la page sur laquelle tu arrives en visitant beat-cut.com."],
          ["Créer un compte / Connexion", "Inscription en 30 secondes avec Google ou par email + mot de passe. Tu y coches les CGV et, si tu veux, la newsletter. Un lien « Mot de passe oublié ? » permet de recevoir un email de réinitialisation."],
          ["Le Studio", "Le cœur de BeatCut : c'est là que tu déposes ton morceau, ajoutes tes clips, cales tes paroles et exportes ta vidéo. Tout est expliqué en détail plus bas."],
          ["Mes morceaux", "Dans le studio, l'onglet « Morceaux » liste tous tes projets. Chaque morceau garde son montage, ses paroles et son style. Le bouton « Nouveau morceau » crée un projet vierge, et le guide « Bien démarrer » te rappelle les 4 étapes."],
          ["Série de vidéos", "Toujours dans le studio : génère plusieurs variantes d'une même vidéo d'un coup, pour poster tous les jours sans refaire le montage."],
          ["Mon compte", "Ton tableau de bord : abonnement (activer, gérer, annuler en 2 clics), jauge de stockage utilisé, code de parrainage, et suppression définitive du compte si tu le souhaites."],
          ["Contact", "Une question, un bug, une idée ? Écris-nous à contact@beat-cut.com — on répond vite."],
          ["CGV / Confidentialité / Mentions légales", "Les pages légales : conditions de vente, gestion de tes données et informations sur l'éditeur du site."],
        ],
      },
      {
        id: "etapes", title: "Créer une vidéo en 4 étapes",
        intro: "Peu importe ton niveau, le studio suit toujours la même logique :",
        items: [
          ["1 — Dépose ton morceau", "Glisse ton fichier audio (MP3, WAV...). BeatCut détecte automatiquement le tempo et les temps forts."],
          ["2 — Ajoute tes clips", "Importe tes propres vidéos ou pioche dans la banque de clips libres de droits. Elles sont découpées en plans et placées sur le beat automatiquement."],
          ["3 — Paroles et style", "Ajoute tes paroles (détection auto ou collage manuel), puis choisis la police, les couleurs, les effets et les animations."],
          ["4 — Exporte", "Clique sur « Exporter la vidéo » : le fichier MP4 vertical est généré directement dans ton navigateur, prêt à poster."],
        ],
      },
      {
        id: "studio-pc", title: "Le studio sur ordinateur — la barre du haut",
        intro: "Sur PC, une barre d'outils en haut de l'écran donne accès à tout. De gauche à droite :",
        items: [
          ["Logo BEATCUT", "Clic = retour à l'accueil du studio (liste de tes morceaux)."],
          ["Clips", "Ouvre le panneau d'import des vidéos (voir « Panneau Clips » plus bas)."],
          ["Enregistré", "Indicateur de sauvegarde : ton projet est enregistré automatiquement à chaque modification. Tu ne peux rien perdre."],
          ["Thème", "Bascule l'interface entre sombre et clair."],
          ["Annuler", "Annule la dernière action (équivalent Ctrl+Z). Utilisable plusieurs fois d'affilée."],
          ["Versions", "Historique des versions du morceau : BeatCut garde des sauvegardes régulières, tu peux revenir à un état précédent du montage à tout moment."],
          ["Série", "Ouvre le mode « Série de vidéos » pour générer plusieurs variantes d'un coup."],
          ["Style", "Ouvre le panneau Paroles & style (texte, effets, animations)."],
          ["Exporter la vidéo", "Le bouton rouge : lance le rendu final de ta vidéo en MP4."],
        ],
      },
      {
        id: "clips", title: "Panneau Clips",
        intro: "C'est ici que tu gères les images de ta vidéo. Tes vidéos sont découpées en plans et placées sur le beat automatiquement.",
        items: [
          ["Importer des vidéos", "Glisse tes fichiers ou clique pour les sélectionner. Tu peux en importer plusieurs à la fois."],
          ["Plans par vidéo", "« Auto » laisse BeatCut décider combien de plans extraire de chaque vidéo. Tu peux aussi fixer un nombre précis."],
          ["Banque de clips", "Des milliers de vidéos libres de droits, cherchables par mot-clé (voiture, ville, nuit...). Pratique si tu n'as pas tes propres images."],
          ["Récupérer mes vidéos déjà envoyées", "Réutilise les vidéos que tu as importées dans tes autres morceaux, sans les renvoyer."],
          ["Plein écran", "Affiche l'aperçu vidéo en grand (touche F sur PC)."],
        ],
      },
      {
        id: "son", title: "Panneau Son — ton extrait",
        intro: "Ta vidéo ne dure que quelques secondes : ce panneau sert à choisir LE bon extrait de ton morceau.",
        items: [
          ["Dépose ton morceau", "Importe ton fichier audio. Le tempo et les beats sont détectés automatiquement."],
          ["Libre / Trouver le drop", "« Trouver le drop » repère automatiquement le moment le plus fort du morceau. « Libre » te laisse choisir le point de départ à la main."],
          ["Début", "Le point de départ exact de ton extrait dans le morceau."],
          ["Durée (boucle parfaite)", "BeatCut propose une durée qui tombe pile sur un nombre entier de mesures : la vidéo boucle parfaitement quand elle est rejouée."],
          ["Tempo / TAP", "Si le tempo détecté est faux, corrige-le à la main ou tape le bouton TAP en rythme avec le morceau."],
        ],
      },
      {
        id: "paroles", title: "Panneau Paroles",
        intro: "Les paroles s'affichent mot à mot, synchronisées avec la voix.",
        items: [
          ["Détecter les paroles", "BeatCut écoute ton extrait et écrit les paroles automatiquement, avec le bon timing pour chaque mot."],
          ["J'ai mes paroles", "Tu colles ton texte, et BeatCut le cale sur la voix. Plus fiable si ta diction est rapide ou ton texte particulier."],
          ["Caler mes paroles", "Mode manuel : tape en rythme pour poser chaque mot exactement où tu veux."],
          ["Recaler les paroles", "Relance la synchronisation si le calage a glissé après une modification."],
          ["Repartir de zéro", "Efface les paroles actuelles pour recommencer proprement."],
        ],
      },
      {
        id: "style", title: "Panneau Style",
        intro: "Quatre onglets : Styles, Texte, Effets, Animation. C'est ici que ta vidéo prend sa personnalité.",
        items: [
          ["Styles", "Des presets complets prêts à l'emploi. Un clic applique police + couleurs + effets d'un coup. « Enregistrer comme mon style » sauvegarde ton réglage actuel pour le réutiliser sur tes prochains morceaux."],
          ["Texte — Police", "18 polices : impact massif (Anton, Archivo Black), manuscrit (Caveat, Marker), rétro (VT323, Silkscreen), néon (Monoton), gothique (Fraktur), glitché (Rubik Glitch)..."],
          ["Texte — Affichage", "« Mot seul » : un mot à la fois, style TikTok. « Phrase » : la ligne complète. « Étalé » : les mots se répartissent sur l'écran."],
          ["Texte — Réglages", "Taille (jusqu'à MAX), épaisseur (fin / normal / gras), casse (MAJUSCULES), couleur, position (haut / centre / bas), espacement des lettres et inclinaison."],
          ["Karaoké", "« Mot en cours coloré » : le mot chanté prend une couleur différente, comme un karaoké."],
          ["Contour / Lueur / Ombre", "Contour noir ou blanc autour du texte, lueur néon (douce ou forte), ombre portée : tout pour que le texte reste lisible sur n'importe quelle image."],
          ["Lignes CRT / Fond", "« Lignes d'écran rétro » ajoute un effet vieil écran sur le texte. « Fond derrière le texte » pose un bandeau de couleur pour un look sous-titre."],
          ["Mots mis en avant", "Clique sur un mot de tes paroles pour lui donner sa propre taille, sa propre couleur, voire sa propre police. Parfait pour faire ressortir les punchlines."],
          ["Effets vidéo", "Appliqués au rythme des coupures : Flash blanc, Zoom punch, Secousse, Glitch, VHS, Grain, Saturé 4K, Glow, Caméra instable, Fisheye."],
          ["Animation des mots", "Comment chaque mot apparaît : Aucune, Pop, Fondu, Glissé, Zoom ou Secousse — avec un aperçu animé de chaque option. Une case permet de garder le mot affiché jusqu'au suivant."],
        ],
      },
      {
        id: "timeline", title: "La timeline (bas de l'écran sur PC)",
        intro: "La timeline montre tes plans vidéo et tes paroles dans le temps. Deux onglets : « Plans » et « Paroles ».",
        items: [
          ["Couper ici", "Coupe le plan à l'endroit de la tête de lecture, pour le diviser en deux."],
          ["Beat : ON / OFF", "Quand c'est ON, toutes les coupes se calent automatiquement sur les temps forts du morceau. C'est le cœur de BeatCut."],
          ["Mélanger", "Redistribue aléatoirement l'ordre des plans, pour tester une autre version du montage en un clic."],
          ["Sans coupes", "Désactive le découpage : la vidéo joue tes clips en continu, sans coupes sur le beat."],
          ["Verrouiller", "Verrouille le plan sous la tête de lecture : il ne bougera plus quand tu mélanges ou modifies le reste."],
          ["Supprimer / Coller au curseur", "Supprime le plan sélectionné, ou colle un plan copié à la position du curseur."],
          ["Zoomer / Dézoomer / Adapter", "Zoom avant et arrière sur la timeline. « Adapter » (ou « Tout voir ») recadre pour afficher tout l'extrait d'un coup."],
          ["Clic sur un plan", "Sélectionne le plan : tu peux alors le remplacer, changer le moment exact du clip utilisé, le découper ou le supprimer."],
        ],
      },
      {
        id: "mobile", title: "Le studio sur mobile",
        intro: "Sur téléphone, le studio adopte une interface façon CapCut : aperçu en haut, timeline au milieu, barre d'outils en bas.",
        items: [
          ["Barre du bas — Clips", "Importer tes vidéos, ouvrir la banque de clips libres de droits, régler les plans par vidéo."],
          ["Barre du bas — Son", "Déposer ton morceau, choisir le début de l'extrait, trouver le drop, régler le tempo (BPM)."],
          ["Barre du bas — Paroles", "Détection automatique, collage de ton texte ou calage manuel des paroles."],
          ["Barre du bas — Style", "Polices, couleurs, effets vidéo et animations des mots."],
          ["Barre du bas — Plus", "Le menu réglages : Annuler la dernière action, Versions du morceau, Revoir le tutoriel, Aide & guide complet, changer de langue (Français / English), Retour à l'accueil et Mon compte."],
          ["Toucher un plan", "Ouvre la feuille « Ce plan » avec 5 actions : Remplacer le clip, Autre plan (changer le moment du clip utilisé), Découper en 2, Supprimer, et Verrouiller ce plan."],
          ["Menu (3 barres)", "En haut : navigue entre Accueil, Morceaux, Série et Compte."],
        ],
      },
      {
        id: "serie", title: "Série de vidéos",
        intro: "Pour poster tous les jours sans refaire le montage : génère plusieurs variantes d'une même vidéo.",
        items: [
          ["Morceau", "Choisis le projet qui sert de base à la série."],
          ["Nombre de vidéos", "Combien de variantes générer (montages différents, mêmes paroles et même style)."],
          ["Préparer les vidéos", "Lance la génération des variantes. Chacune a un ordre de plans différent."],
          ["Choisir les meilleures", "Regarde chaque variante et coche celles que tu veux garder."],
          ["Exporter la sélection", "Exporte toutes les vidéos cochées d'un coup."],
        ],
      },
      {
        id: "export", title: "Exporter sa vidéo",
        intro: "L'export se fait directement dans ton navigateur : rien n'est envoyé sur un serveur pour le rendu.",
        items: [
          ["Exporter la vidéo", "Le bouton rouge en haut à droite (PC) lance le rendu. Une barre de progression s'affiche, puis le fichier MP4 se télécharge."],
          ["Format", "Vidéo verticale 9:16, optimisée pour TikTok, Reels et Shorts. Le format est réglable via le bouton « Format de la vidéo » près de l'aperçu."],
          ["Filigrane", "Sur le plan gratuit, un filigrane BeatCut est ajouté à l'export. Il disparaît avec un abonnement (7 jours d'essai offerts sur le plan Pro)."],
          ["Exports restants", "Ton compteur d'exports du mois est visible dans la barre du studio. Il se remet à zéro chaque mois selon ton plan."],
        ],
      },
      {
        id: "raccourcis", title: "Raccourcis clavier (PC)", intro: null,
        items: [
          ["Espace", "Lecture / pause de l'aperçu."],
          ["Ctrl + Z", "Annuler la dernière action."],
          ["F", "Aperçu en plein écran."],
        ],
      },
    ],
  },
  en: {
    eyebrow: "[ HELP ]",
    title: "Understand everything about BeatCut.",
    lead: "BeatCut turns your track into beat-synced videos, ready for TikTok, Reels and Shorts. This page explains every page of the site and every button in the studio, on desktop and on mobile.",
    contactTitle: "Still have a question?",
    contactText: "We answer every email, usually the same day.",
    contactBtn: "Email contact@beat-cut.com",
    sections: [
      {
        id: "pages", title: "The pages of the site",
        intro: "The site is made of a few simple pages. Here is what each one does.",
        items: [
          ["Home", "BeatCut's storefront: overview, examples, pricing and the button to get started. It's the page you land on when visiting beat-cut.com."],
          ["Sign up / Sign in", "30-second signup with Google or email + password. You accept the Terms and, if you want, the newsletter. A \"Forgot password?\" link sends you a reset email."],
          ["The Studio", "The heart of BeatCut: where you drop your track, add your clips, sync your lyrics and export your video. Everything is detailed below."],
          ["My tracks", "Inside the studio, the \"Tracks\" tab lists all your projects. Each track keeps its edit, lyrics and style. The \"New track\" button creates a blank project, and the \"Getting started\" guide reminds you of the 4 steps."],
          ["Video series", "Also in the studio: generate several variants of the same video at once, to post every day without redoing the edit."],
          ["My account", "Your dashboard: subscription (activate, manage, cancel in 2 clicks), storage gauge, referral code, and permanent account deletion if you wish."],
          ["Contact", "A question, a bug, an idea? Write to contact@beat-cut.com — we answer fast."],
          ["Terms / Privacy / Legal notice", "The legal pages: terms of sale, how your data is handled and publisher information."],
        ],
      },
      {
        id: "etapes", title: "Create a video in 4 steps",
        intro: "Whatever your level, the studio always follows the same logic:",
        items: [
          ["1 — Drop your track", "Drag your audio file (MP3, WAV...). BeatCut automatically detects the tempo and the strong beats."],
          ["2 — Add your clips", "Import your own videos or pick from the royalty-free clip library. They are cut into shots and placed on the beat automatically."],
          ["3 — Lyrics and style", "Add your lyrics (auto detection or paste them), then pick the font, colors, effects and animations."],
          ["4 — Export", "Click \"Export video\": the vertical MP4 file is generated right in your browser, ready to post."],
        ],
      },
      {
        id: "studio-pc", title: "The studio on desktop — the top bar",
        intro: "On desktop, a toolbar at the top of the screen gives access to everything. From left to right:",
        items: [
          ["BEATCUT logo", "Click = back to the studio home (your track list)."],
          ["Clips", "Opens the video import panel (see \"Clips panel\" below)."],
          ["Saved", "Save indicator: your project is saved automatically after every change. You can't lose anything."],
          ["Theme", "Switches the interface between dark and light."],
          ["Undo", "Undoes the last action (same as Ctrl+Z). Can be used several times in a row."],
          ["Versions", "Track version history: BeatCut keeps regular backups, you can go back to a previous state of the edit at any time."],
          ["Series", "Opens the \"Video series\" mode to generate several variants at once."],
          ["Style", "Opens the Lyrics & style panel (text, effects, animations)."],
          ["Export video", "The red button: starts the final MP4 render of your video."],
        ],
      },
      {
        id: "clips", title: "Clips panel",
        intro: "This is where you manage the visuals of your video. Your videos are cut into shots and placed on the beat automatically.",
        items: [
          ["Import videos", "Drag your files or click to select them. You can import several at once."],
          ["Shots per video", "\"Auto\" lets BeatCut decide how many shots to extract from each video. You can also set an exact number."],
          ["Clip library", "Thousands of royalty-free videos, searchable by keyword (car, city, night...). Handy if you don't have your own footage."],
          ["Get my uploaded videos", "Reuse the videos you imported in your other tracks, without re-uploading them."],
          ["Fullscreen", "Shows the video preview in large (F key on desktop)."],
        ],
      },
      {
        id: "son", title: "Sound panel — your extract",
        intro: "Your video only lasts a few seconds: this panel is for picking THE right extract of your track.",
        items: [
          ["Drop your track", "Import your audio file. Tempo and beats are detected automatically."],
          ["Free / Find the drop", "\"Find the drop\" automatically spots the strongest moment of the track. \"Free\" lets you pick the start point by hand."],
          ["Start", "The exact starting point of your extract within the track."],
          ["Length (perfect loop)", "BeatCut suggests a length that lands exactly on a whole number of bars: the video loops perfectly when replayed."],
          ["Tempo / TAP", "If the detected tempo is wrong, fix it by hand or hit the TAP button in rhythm with the track."],
        ],
      },
      {
        id: "paroles", title: "Lyrics panel",
        intro: "Lyrics appear word by word, synced to the vocals.",
        items: [
          ["Detect lyrics", "BeatCut listens to your extract and writes the lyrics automatically, with the right timing for each word."],
          ["I have my lyrics", "You paste your text, and BeatCut syncs it to the vocals. More reliable if your delivery is fast or your text is unusual."],
          ["Sync my lyrics", "Manual mode: tap in rhythm to place each word exactly where you want."],
          ["Re-sync lyrics", "Re-runs the sync if the timing drifted after an edit."],
          ["Start over", "Clears the current lyrics to start fresh."],
        ],
      },
      {
        id: "style", title: "Style panel",
        intro: "Four tabs: Styles, Text, Effects, Animation. This is where your video gets its personality.",
        items: [
          ["Styles", "Complete ready-to-use presets. One click applies font + colors + effects at once. \"Save as my style\" stores your current setup to reuse on your next tracks."],
          ["Text — Font", "18 fonts: heavy impact (Anton, Archivo Black), handwritten (Caveat, Marker), retro (VT323, Silkscreen), neon (Monoton), gothic (Fraktur), glitched (Rubik Glitch)..."],
          ["Text — Display", "\"Single word\": one word at a time, TikTok style. \"Sentence\": the full line. \"Spread\": words spread across the screen."],
          ["Text — Settings", "Size (up to MAX), weight (thin / normal / bold), case (UPPERCASE), color, position (top / center / bottom), letter spacing and tilt."],
          ["Karaoke", "\"Current word colored\": the word being sung takes a different color, like karaoke."],
          ["Outline / Glow / Shadow", "Black or white outline around the text, neon glow (soft or strong), drop shadow: everything to keep the text readable on any footage."],
          ["CRT lines / Background", "\"Retro screen lines\" adds an old-screen effect on the text. \"Background behind text\" adds a color band for a subtitle look."],
          ["Highlighted words", "Click a word in your lyrics to give it its own size, color, even its own font. Perfect to make punchlines stand out."],
          ["Video effects", "Applied on the rhythm of the cuts: White flash, Zoom punch, Shake, Glitch, VHS, Grain, Saturated 4K, Glow, Handheld camera, Fisheye."],
          ["Word animation", "How each word appears: None, Pop, Fade, Slide, Zoom or Shake — with an animated preview of each option. A checkbox keeps the word on screen until the next one."],
        ],
      },
      {
        id: "timeline", title: "The timeline (bottom of the screen on desktop)",
        intro: "The timeline shows your video shots and lyrics over time. Two tabs: \"Shots\" and \"Lyrics\".",
        items: [
          ["Cut here", "Cuts the shot at the playhead position, splitting it in two."],
          ["Beat: ON / OFF", "When ON, every cut automatically snaps to the strong beats of the track. That's the heart of BeatCut."],
          ["Shuffle", "Randomly redistributes the order of the shots, to try another version of the edit in one click."],
          ["No cuts", "Disables the cutting: the video plays your clips continuously, without beat cuts."],
          ["Lock", "Locks the shot under the playhead: it won't move when you shuffle or edit the rest."],
          ["Delete / Paste at cursor", "Deletes the selected shot, or pastes a copied shot at the cursor position."],
          ["Zoom in / Zoom out / Fit", "Zooms the timeline in and out. \"Fit\" reframes to show the whole extract at once."],
          ["Click a shot", "Selects the shot: you can then swap it, change the exact moment of the clip used, split it or delete it."],
        ],
      },
      {
        id: "mobile", title: "The studio on mobile",
        intro: "On the phone, the studio uses a CapCut-style interface: preview on top, timeline in the middle, toolbar at the bottom.",
        items: [
          ["Bottom bar — Clips", "Import your videos, open the royalty-free clip library, set shots per video."],
          ["Bottom bar — Sound", "Drop your track, pick the extract start, find the drop, set the tempo (BPM)."],
          ["Bottom bar — Lyrics", "Auto detection, paste your text or manual lyric syncing."],
          ["Bottom bar — Style", "Fonts, colors, video effects and word animations."],
          ["Bottom bar — More", "The settings menu: Undo last action, Track versions, Replay the tutorial, Help & full guide, switch language (Français / English), Back to home and My account."],
          ["Tap a shot", "Opens the \"This shot\" sheet with 5 actions: Swap clip, Another shot (change the moment of the clip used), Split in 2, Delete, and Lock this shot."],
          ["Menu (3 bars)", "At the top: navigate between Home, Tracks, Series and Account."],
        ],
      },
      {
        id: "serie", title: "Video series",
        intro: "To post every day without redoing the edit: generate several variants of the same video.",
        items: [
          ["Track", "Pick the project that serves as the base of the series."],
          ["Number of videos", "How many variants to generate (different edits, same lyrics and style)."],
          ["Prepare the videos", "Starts generating the variants. Each one has a different shot order."],
          ["Pick the best ones", "Watch each variant and check the ones you want to keep."],
          ["Export the selection", "Exports all checked videos at once."],
        ],
      },
      {
        id: "export", title: "Exporting your video",
        intro: "The export happens right in your browser: nothing is sent to a server for rendering.",
        items: [
          ["Export video", "The red button at the top right (desktop) starts the render. A progress bar appears, then the MP4 file downloads."],
          ["Format", "Vertical 9:16 video, optimized for TikTok, Reels and Shorts. The format can be changed via the \"Video format\" button near the preview."],
          ["Watermark", "On the free plan, a BeatCut watermark is added to the export. It disappears with a subscription (7-day free trial on the Pro plan)."],
          ["Exports left", "Your monthly export counter is visible in the studio bar. It resets every month according to your plan."],
        ],
      },
      {
        id: "raccourcis", title: "Keyboard shortcuts (desktop)", intro: null,
        items: [
          ["Space", "Play / pause the preview."],
          ["Ctrl + Z", "Undo the last action."],
          ["F", "Fullscreen preview."],
        ],
      },
    ],
  },
};

function Item({ name, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 py-2.5 border-b border-border/50 last:border-0">
      <span className="font-osd text-[11px] tracking-[0.12em] uppercase text-primary shrink-0 sm:w-56">{name}</span>
      <span className="text-sm text-muted-foreground leading-relaxed">{children}</span>
    </div>
  );
}

export default function Aide() {
  const { lang } = useI18n();
  const c = CONTENT[lang] || CONTENT.fr;
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar />
      <main className="flex-1 mx-auto w-full max-w-5xl px-5 sm:px-8 py-12">
        <p className="font-osd text-xs tracking-[0.25em] text-primary mb-3">{c.eyebrow}</p>
        <h1 className="font-display text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">{c.title}</h1>
        <p className="text-sm text-muted-foreground max-w-2xl mb-8 leading-relaxed">{c.lead}</p>

        <nav className="flex flex-wrap gap-2 mb-10" data-testid="aide-toc">
          {c.sections.map((s) => (
            <a key={s.id} href={`#${s.id}`}
              className="border border-border px-3 py-1.5 text-[11px] font-osd tracking-wider uppercase text-muted-foreground hover:border-foreground hover:text-foreground transition-colors">
              {s.title}
            </a>
          ))}
        </nav>

        {c.sections.map((s) => (
          <section key={s.id} id={s.id} className="scroll-mt-20 bg-card border border-border p-6 sm:p-8 mb-6" data-testid={`aide-section-${s.id}`}>
            <h2 className="font-display text-xl font-bold mb-2">{s.title}</h2>
            {s.intro && <p className="text-sm text-muted-foreground mb-5 max-w-3xl leading-relaxed">{s.intro}</p>}
            {s.items.map(([name, text]) => (
              <Item key={name} name={name}>{text}</Item>
            ))}
          </section>
        ))}

        <div className="bg-card border border-primary p-6 sm:p-8 text-center">
          <p className="font-display text-lg font-bold mb-2">{c.contactTitle}</p>
          <p className="text-sm text-muted-foreground mb-4">{c.contactText}</p>
          <a href="mailto:contact@beat-cut.com" data-testid="aide-contact-button"
            className="inline-block bg-primary text-white font-bold px-6 py-3 hover:opacity-90 transition-opacity">
            {c.contactBtn}
          </a>
        </div>
      </main>
      <Footer />
    </div>
  );
}
