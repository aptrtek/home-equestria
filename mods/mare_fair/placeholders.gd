extends RefCounted
## The Mare Fair mascots (https://marefair.org/mascots/).
## Cutie marks are the public vectors from the 2025 site icon set, rendered to PNG
## and stored transposed, the way every other flank sheet in this game is stored.
## Manes and tails are original shells on the game's hair bones, shaped after the
## public portraits and the 2025 idle clips. Clothes, glasses and the balloon
## are still stand-ins. The reference pictures are not shipped.

const IDS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]

## The 2025 desktop picture shows the balloon: red and light-blue vertical gores, a red
## basket, and a light-blue star. That picture is cropped through the top of the envelope,
## so no crown emblem was invented. The PNG is not shipped. The balloon stays parked.
const BALLOON := "Parked on Balloon Hill, apart from Twilight's flyable balloon. Envelope is an original lathed shape with eight red and light-blue gores, sampled from https://2025.marefair.org/_astro/mf_desktop.iPluWSMU_EDpGb.png. Basket is red with a light-blue star on each side and a front ramp so ponies can step in. The reference crops the top, so the crown is only the stripes closing. Not a second aircraft."

## What a player should be told is unfinished, keyed by identity id.
const NOTES := {
	"fair_flyer": "Pegasus, from the official portrait (wings; the written bio says she soars and does not name the race). Coat is the blue-grey body colour. Mane is long two-tone blonde with a dusky tip, under her wide sun hat with its blue ribbon and sunflower; tail is the big wavy blonde one. The purple belly is not on the model. Cutie mark is the official vector: an orange star in a blue ring, with orange and blue dots on a pale wheel.",
	"soiree": "Earth pony, from her bio. Coat pale yellow, eyes magenta. Mane is a smooth rounded cyan bob with a level fringe and side locks that curl forward at the jaw; tail is a short cyan crescent on the rump. Cutie mark is the official vector: a white frowning theatre mask beside a yellow crescent.",
	"matinee": "Pegasus, from her bio. Coat pale yellow, eyes magenta. Mane is swept light blue with a high ponytail in a pink scrunchie; the tail ends in purple. Cutie mark is the official vector: a yellow sunburst behind a white smiling theatre mask.",
	"morning_mimosa": "Earth pony, from her bio. Coat peach, eyes gold. Mane is green with a cowlick, an orange slice by the ear and a long leafy side braid tied with an orange; tail is the same leafy braid with an orange tie. She wears her round spiral glasses. The gold bangles are not on the model. Cutie mark is the official vector: a champagne flute with an orange slice on the rim.",
	"fun_raiser": "Unicorn, from the official portrait (horn and pale green coat). The written bio does not name her race. Eyes green. Mane is the orange high ponytail with a green band, a pale streak and a curled side lock; tail is the thick curled orange one with a pale streak. She wears her gold half-moon reading glasses. The white jacket and pendant are not on the model. Cutie mark is the official vector: a grey hotel beside a palm.",
}
