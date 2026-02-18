const POKEAPI_BASE = 'https://pokeapi.co/api/v2';

const check = async () => {
    try {
        const response = await fetch(`${POKEAPI_BASE}/pokemon?limit=10000`);
        const data = await response.json();

        const regular = data.results.filter(p => !p.url.includes('/pokemon/10') && !p.url.includes('/pokemon/11') && !p.url.includes('/pokemon/12'));
        // IDs > 10000 are usually forms.
        // Let's see what the count is.

        const forms = data.results.filter(p => {
            const id = parseInt(p.url.split('/').filter(Boolean).pop() || '0');
            return id >= 10000;
        });

        console.log(`Regular count: ${regular.length}`);
        console.log(`Forms count: ${forms.length}`);
        console.log(`First 5 forms:`, forms.slice(0, 5));

    } catch (error) {
        console.error('Failed', error);
    }
};

check();
