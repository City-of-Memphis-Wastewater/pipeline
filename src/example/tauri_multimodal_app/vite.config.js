import { defineConfig } from 'vite';

export default defineConfig({
  root: 'dist',  // <-- look for index.html here # no this is dumb, thats a build folder not a templates folder
  build: {
    outDir: '../dist-build', // output folder for Vite build, can be src-tauri/../dist-build
    emptyOutDir: true
  }
});
