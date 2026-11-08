extends RefCounted
## The Mare Fair mascots (https://marefair.org/mascots/).
## Cutie marks are the public vectors from the 2025 site icon set, rendered to PNG.
## Hair, clothes and the balloon are still stand-ins. The balloon reference PNG is not shipped.

const IDS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]

## The 2025 desktop picture shows the balloon: red and light-blue vertical gores, a red
## basket, and a light-blue star. That picture is cropped through the top of the envelope,
## so no crown emblem was invented. The PNG is not shipped. The balloon stays parked.
const BALLOON := "Parked on Balloon Hill, apart from Twilight's flyable balloon. Envelope is an original lathed shape with eight red and light-blue gores, sampled from https://2025.marefair.org/_astro/mf_desktop.iPluWSMU_EDpGb.png. Basket is red with a light-blue star on each side and a front ramp so ponies can step in. The reference crops the top, so the crown is only the stripes closing. Not a second aircraft."

## What a player should be told is unfinished, keyed by identity id.
const NOTES := {
	"fair_flyer": "Pegasus, from the official portrait (wings; the written bio says she soars and does not name the race). Coat is the blue-grey body colour. The purple belly and legs, blonde-and-pink mane tips, blue headband and sunflower hat are not on the model. Hair is Lily Valley's mesh, recolored blonde. Cutie mark is the official vector: an orange star in a blue ring, with orange and blue dots on a pale wheel.",
	"soiree": "Earth pony, from her bio. Coat pale yellow, mane cyan, eyes magenta. Hair is Bon Bon's mesh, recolored; the short swept style and any curls are not hers. Cutie mark is the official vector: a white frowning theatre mask beside a yellow crescent.",
	"matinee": "Pegasus, from her bio. Coat pale yellow, mane light blue, eyes magenta. The purple streak and purple tail on the portrait are one recolor, so they are not separate. Hair is Cloudchaser's mesh. Cutie mark is the official vector: a yellow sunburst behind a white smiling theatre mask.",
	"morning_mimosa": "Earth pony, from her bio. Coat peach, mane the flat green of the portrait, eyes gold. The orange-slice hair clip, leafy tail ties and gold bangles are not on the model. Hair is Golden Harvest's mesh, recolored green. Glasses, when the Vinyl Scratch glasses file is installed with the source data, are that mesh and not her round frames. Cutie mark is the official vector: a champagne flute with an orange slice on the rim.",
	"fun_raiser": "Unicorn, from the official portrait (horn and pale green coat). The written bio does not name her race. Mane orange, eyes green. The high ponytail, white jacket and pendant are not on the model. Hair is Spitfire's swept mesh, recolored orange, which is not a ponytail. Glasses use Vinyl Scratch's frames when that file is installed. Cutie mark is the official vector: a grey hotel beside a palm.",
}
