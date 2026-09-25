import {fileURLToPath} from 'node:url';
import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/postcss';
const path=(relative:string)=>fileURLToPath(new URL(relative,import.meta.url));
// Builds into ../pbpk-atlas, served by GitHub Pages next to ../human-atlas, whose models it reuses.
export default defineConfig({root:path('./web'),base:'./',publicDir:path('./public'),plugins:[react()],resolve:{alias:{'@':path('./')}},css:{postcss:{plugins:[tailwindcss()]}},server:{watch:{usePolling:true}},build:{outDir:path('../pbpk-atlas'),emptyOutDir:true,chunkSizeWarningLimit:1200}});
