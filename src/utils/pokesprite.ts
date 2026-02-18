export const getPokespriteUrl = (name: string, shiny: boolean = false): string => {
    // Pokesprite uses specific naming conventions. 
    // We might need to handle special cases, but for now we'll assume the name matches.
    // Using the raw github user content.
    const baseUrl = 'https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen8';
    const type = shiny ? 'shiny' : 'regular';

    // Clean name: specific corrections might be needed for special characters or forms
    // e.g. "nidoran-m" -> "nidoran-m", but "farfetch'd" -> "farfetchd"?
    // Pokesprite usually keeps dashes but removes special chars.
    let cleanName = name.toLowerCase()
        .replace(/[.'’]/g, '') // remove dots, apostrophes
        .replace(/ /g, '-');   // spaces to dashes

    // TODO: Add specific overrides map if we find broken images
    // Special handling for Nidoran
    if (cleanName === 'nidoran-m') cleanName = 'nidoran-m';
    if (cleanName === 'nidoran-f') cleanName = 'nidoran-f';


    // Using PNGs
    return `${baseUrl}/${type}/${cleanName}.png`;
};
