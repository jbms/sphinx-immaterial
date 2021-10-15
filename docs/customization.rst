:hero: Configuration options to personalize your site.

.. embedded material icons used for inline demonstration
.. raw:: html

    <style>
    .inline-icon {
        background-color: var(--md-default-fg-color);
        mask-repeat: no-repeat;
        mask-size: contain;
        display: inline-block;
        height: 1.2rem;
        width: 1.2rem;
    }
    .eye { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 9a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5 5 5 0 0 1 5-5 5 5 0 0 1 5 5 5 5 0 0 1-5 5m0-12.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5z"/></svg>');}
    .eye-outline { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 9a3 3 0 0 1 3 3 3 3 0 0 1-3 3 3 3 0 0 1-3-3 3 3 0 0 1 3-3m0-4.5c5 0 9.27 3.11 11 7.5-1.73 4.39-6 7.5-11 7.5S2.73 16.39 1 12c1.73-4.39 6-7.5 11-7.5M3.18 12a9.821 9.821 0 0 0 17.64 0 9.821 9.821 0 0 0-17.64 0z"/></svg>');}
    .lightbulb { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7M9 21a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-1H9v1z"/></svg>');}
    .lightbulb-outline { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7M9 21v-1h6v1a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1m3-17a5 5 0 0 0-5 5c0 2.05 1.23 3.81 3 4.58V16h4v-2.42c1.77-.77 3-2.53 3-4.58a5 5 0 0 0-5-5z"/></svg>');}
    .sunny { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 7a5 5 0 0 1 5 5 5 5 0 0 1-5 5 5 5 0 0 1-5-5 5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3m0-7 2.39 3.42C13.65 5.15 12.84 5 12 5c-.84 0-1.65.15-2.39.42L12 2M3.34 7l4.16-.35A7.2 7.2 0 0 0 5.94 8.5c-.44.74-.69 1.5-.83 2.29L3.34 7m.02 10 1.76-3.77a7.131 7.131 0 0 0 2.38 4.14L3.36 17M20.65 7l-1.77 3.79a7.023 7.023 0 0 0-2.38-4.15l4.15.36m-.01 10-4.14.36c.59-.51 1.12-1.14 1.54-1.86.42-.73.69-1.5.83-2.29L20.64 17M12 22l-2.41-3.44c.74.27 1.55.44 2.41.44.82 0 1.63-.17 2.37-.44L12 22z"/></svg>');}
    .night { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m17.75 4.09-2.53 1.94.91 3.06-2.63-1.81-2.63 1.81.91-3.06-2.53-1.94L12.44 4l1.06-3 1.06 3 3.19.09m3.5 6.91-1.64 1.25.59 1.98-1.7-1.17-1.7 1.17.59-1.98L15.75 11l2.06-.05L18.5 9l.69 1.95 2.06.05m-2.28 4.95c.83-.08 1.72 1.1 1.19 1.85-.32.45-.66.87-1.08 1.27C15.17 23 8.84 23 4.94 19.07c-3.91-3.9-3.91-10.24 0-14.14.4-.4.82-.76 1.27-1.08.75-.53 1.93.36 1.85 1.19-.27 2.86.69 5.83 2.89 8.02a9.96 9.96 0 0 0 8.02 2.89m-1.64 2.02a12.08 12.08 0 0 1-7.8-3.47c-2.17-2.19-3.33-5-3.49-7.82-2.81 3.14-2.7 7.96.31 10.98 3.02 3.01 7.84 3.12 10.98.31z"/></svg>');}
    .toggle-off { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M7 10a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2m10-3a5 5 0 0 1 5 5 5 5 0 0 1-5 5H7a5 5 0 0 1-5-5 5 5 0 0 1 5-5h10M7 9a3 3 0 0 0-3 3 3 3 0 0 0 3 3h10a3 3 0 0 0 3-3 3 3 0 0 0-3-3H7z"/></svg>');}
    .toggle-on { mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17 7H7a5 5 0 0 0-5 5 5 5 0 0 0 5 5h10a5 5 0 0 0 5-5 5 5 0 0 0-5-5m0 8a3 3 0 0 1-3-3 3 3 0 0 1 3-3 3 3 0 0 1 3 3 3 3 0 0 1-3 3z"/></svg>');}
    .fa-git {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M216.29 158.39H137C97 147.9 6.51 150.63 6.51 233.18c0 30.09 15 51.23 35 61-25.1 23-37 33.85-37 49.21 0 11 4.47 21.14 17.89 26.81C8.13 383.61 0 393.35 0 411.65c0 32.11 28.05 50.82 101.63 50.82 70.75 0 111.79-26.42 111.79-73.18 0-58.66-45.16-56.5-151.63-63l13.43-21.55c27.27 7.58 118.7 10 118.7-67.89 0-18.7-7.73-31.71-15-41.07l37.41-2.84zm-63.42 241.9c0 32.06-104.89 32.1-104.89 2.43 0-8.14 5.27-15 10.57-21.54 77.71 5.3 94.32 3.37 94.32 19.11zm-50.81-134.58c-52.8 0-50.46-71.16 1.2-71.16 49.54 0 50.82 71.16-1.2 71.16zm133.3 100.51v-32.1c26.75-3.66 27.24-2 27.24-11V203.61c0-8.5-2.05-7.38-27.24-16.26l4.47-32.92H324v168.71c0 6.51.4 7.32 6.51 8.14l20.73 2.84v32.1zm52.45-244.31c-23.17 0-36.59-13.43-36.59-36.61s13.42-35.77 36.59-35.77c23.58 0 37 12.62 37 35.77s-13.42 36.61-37 36.61zM512 350.46c-17.49 8.53-43.1 16.26-66.28 16.26-48.38 0-66.67-19.5-66.67-65.46V194.75c0-5.42 1.05-4.06-31.71-4.06V154.5c35.78-4.07 50-22 54.47-66.27h38.63c0 65.83-1.34 61.81 3.26 61.81H501v40.65h-60.56v97.15c0 6.92-4.92 51.41 60.57 26.84z"/></svg>');}
    .fa-git-alt {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M439.55 236.05 244 40.45a28.87 28.87 0 0 0-40.81 0l-40.66 40.63 51.52 51.52c27.06-9.14 52.68 16.77 43.39 43.68l49.66 49.66c34.23-11.8 61.18 31 35.47 56.69-26.49 26.49-70.21-2.87-56-37.34L240.22 199v121.85c25.3 12.54 22.26 41.85 9.08 55a34.34 34.34 0 0 1-48.55 0c-17.57-17.6-11.07-46.91 11.25-56v-123c-20.8-8.51-24.6-30.74-18.64-45L142.57 101 8.45 235.14a28.86 28.86 0 0 0 0 40.81l195.61 195.6a28.86 28.86 0 0 0 40.8 0l194.69-194.69a28.86 28.86 0 0 0 0-40.81z"/></svg>');}
    .fa-git-square {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M100.59 334.24c48.57 3.31 58.95 2.11 58.95 11.94 0 20-65.55 20.06-65.55 1.52.01-5.09 3.29-9.4 6.6-13.46zm27.95-116.64c-32.29 0-33.75 44.47-.75 44.47 32.51 0 31.71-44.47.75-44.47zM448 80v352a48 48 0 0 1-48 48H48a48 48 0 0 1-48-48V80a48 48 0 0 1 48-48h352a48 48 0 0 1 48 48zm-227 69.31c0 14.49 8.38 22.88 22.86 22.88 14.74 0 23.13-8.39 23.13-22.88S258.62 127 243.88 127c-14.48 0-22.88 7.84-22.88 22.31zM199.18 195h-49.55c-25-6.55-81.56-4.85-81.56 46.75 0 18.8 9.4 32 21.85 38.11C74.23 294.23 66.8 301 66.8 310.6c0 6.87 2.79 13.22 11.18 16.76-8.9 8.4-14 14.48-14 25.92C64 373.35 81.53 385 127.52 385c44.22 0 69.87-16.51 69.87-45.73 0-36.67-28.23-35.32-94.77-39.38l8.38-13.43c17 4.74 74.19 6.23 74.19-42.43 0-11.69-4.83-19.82-9.4-25.67l23.38-1.78zm84.34 109.84-13-1.78c-3.82-.51-4.07-1-4.07-5.09V192.52h-52.6l-2.79 20.57c15.75 5.55 17 4.86 17 10.17V298c0 5.62-.31 4.58-17 6.87v20.06h72.42zM384 315l-6.87-22.37c-40.93 15.37-37.85-12.41-37.85-16.73v-60.72h37.85v-25.41h-35.82c-2.87 0-2 2.52-2-38.63h-24.18c-2.79 27.7-11.68 38.88-34 41.42v22.62c20.47 0 19.82-.85 19.82 2.54v66.57c0 28.72 11.43 40.91 41.67 40.91 14.45 0 30.45-4.83 41.38-10.2z"/></svg>');}
    .fa-github {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512"><path d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3.7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3.3 2.9 2.3 3.9 1.6 1 3.6.7 4.3-.7.7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3.7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3.7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"/></svg>');}
    .fa-github-alt {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 512"><path d="M186.1 328.7c0 20.9-10.9 55.1-36.7 55.1s-36.7-34.2-36.7-55.1 10.9-55.1 36.7-55.1 36.7 34.2 36.7 55.1zM480 278.2c0 31.9-3.2 65.7-17.5 95-37.9 76.6-142.1 74.8-216.7 74.8-75.8 0-186.2 2.7-225.6-74.8-14.6-29-20.2-63.1-20.2-95 0-41.9 13.9-81.5 41.5-113.6-5.2-15.8-7.7-32.4-7.7-48.8 0-21.5 4.9-32.3 14.6-51.8 45.3 0 74.3 9 108.8 36 29-6.9 58.8-10 88.7-10 27 0 54.2 2.9 80.4 9.2 34-26.7 63-35.2 107.8-35.2 9.8 19.5 14.6 30.3 14.6 51.8 0 16.4-2.6 32.7-7.7 48.2 27.5 32.4 39 72.3 39 114.2zm-64.3 50.5c0-43.9-26.7-82.6-73.5-82.6-18.9 0-37 3.4-56 6-14.9 2.3-29.8 3.2-45.1 3.2-15.2 0-30.1-.9-45.1-3.2-18.7-2.6-37-6-56-6-46.8 0-73.5 38.7-73.5 82.6 0 87.8 80.4 101.3 150.4 101.3h48.2c70.3 0 150.6-13.4 150.6-101.3zm-82.6-55.1c-25.8 0-36.7 34.2-36.7 55.1s10.9 55.1 36.7 55.1 36.7-34.2 36.7-55.1-10.9-55.1-36.7-55.1z"/></svg>');}
    .fa-github-square {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M400 32H48C21.5 32 0 53.5 0 80v352c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V80c0-26.5-21.5-48-48-48zM277.3 415.7c-8.4 1.5-11.5-3.7-11.5-8 0-5.4.2-33 .2-55.3 0-15.6-5.2-25.5-11.3-30.7 37-4.1 76-9.2 76-73.1 0-18.2-6.5-27.3-17.1-39 1.7-4.3 7.4-22-1.7-45-13.9-4.3-45.7 17.9-45.7 17.9-13.2-3.7-27.5-5.6-41.6-5.6-14.1 0-28.4 1.9-41.6 5.6 0 0-31.8-22.2-45.7-17.9-9.1 22.9-3.5 40.6-1.7 45-10.6 11.7-15.6 20.8-15.6 39 0 63.6 37.3 69 74.3 73.1-4.8 4.3-9.1 11.7-10.6 22.3-9.5 4.3-33.8 11.7-48.3-13.9-9.1-15.8-25.5-17.1-25.5-17.1-16.2-.2-1.1 10.2-1.1 10.2 10.8 5 18.4 24.2 18.4 24.2 9.7 29.7 56.1 19.7 56.1 19.7 0 13.9.2 36.5.2 40.6 0 4.3-3 9.5-11.5 8-66-22.1-112.2-84.9-112.2-158.3 0-91.8 70.2-161.5 162-161.5S388 165.6 388 257.4c.1 73.4-44.7 136.3-110.7 158.3zm-98.1-61.1c-1.9.4-3.7-.4-3.9-1.7-.2-1.5 1.1-2.8 3-3.2 1.9-.2 3.7.6 3.9 1.9.3 1.3-1 2.6-3 3zm-9.5-.9c0 1.3-1.5 2.4-3.5 2.4-2.2.2-3.7-.9-3.7-2.4 0-1.3 1.5-2.4 3.5-2.4 1.9-.2 3.7.9 3.7 2.4zm-13.7-1.1c-.4 1.3-2.4 1.9-4.1 1.3-1.9-.4-3.2-1.9-2.8-3.2.4-1.3 2.4-1.9 4.1-1.5 2 .6 3.3 2.1 2.8 3.4zm-12.3-5.4c-.9 1.1-2.8.9-4.3-.6-1.5-1.3-1.9-3.2-.9-4.1.9-1.1 2.8-.9 4.3.6 1.3 1.3 1.8 3.3.9 4.1zm-9.1-9.1c-.9.6-2.6 0-3.7-1.5s-1.1-3.2 0-3.9c1.1-.9 2.8-.2 3.7 1.3 1.1 1.5 1.1 3.3 0 4.1zm-6.5-9.7c-.9.9-2.4.4-3.5-.6-1.1-1.3-1.3-2.8-.4-3.5.9-.9 2.4-.4 3.5.6 1.1 1.3 1.3 2.8.4 3.5zm-6.7-7.4c-.4.9-1.7 1.1-2.8.4-1.3-.6-1.9-1.7-1.5-2.6.4-.6 1.5-.9 2.8-.4 1.3.7 1.9 1.8 1.5 2.6z"/></svg>');}
    .fa-gitlab {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M105.2 24.9c-3.1-8.9-15.7-8.9-18.9 0L29.8 199.7h132c-.1 0-56.6-174.8-56.6-174.8zM.9 287.7c-2.6 8 .3 16.9 7.1 22l247.9 184-226.2-294zm160.8-88 94.3 294 94.3-294zm349.4 88-28.8-88-226.3 294 247.9-184c6.9-5.1 9.7-14 7.2-22zM425.7 24.9c-3.1-8.9-15.7-8.9-18.9 0l-56.6 174.8h132z"/></svg>');}
    .fa-gitkraken {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 592 512"><path d="M565.7 118.1c-2.3-6.1-9.3-9.2-15.3-6.6-5.7 2.4-8.5 8.9-6.3 14.6 10.9 29 16.9 60.5 16.9 93.3 0 134.6-100.3 245.7-230.2 262.7V358.4c7.9-1.5 15.5-3.6 23-6.2v104c106.7-25.9 185.9-122.1 185.9-236.8 0-91.8-50.8-171.8-125.8-213.3-5.7-3.2-13-.9-15.9 5-2.7 5.5-.6 12.2 4.7 15.1 67.9 37.6 113.9 110 113.9 193.2 0 93.3-57.9 173.1-139.8 205.4v-92.2c14.2-4.5 24.9-17.7 24.9-33.5 0-13.1-6.8-24.4-17.3-30.5 8.3-79.5 44.5-58.6 44.5-83.9V170c0-38-87.9-161.8-129-164.7-2.5-.2-5-.2-7.6 0C251.1 8.3 163.2 132 163.2 170v14.8c0 25.3 36.3 4.3 44.5 83.9-10.6 6.1-17.3 17.4-17.3 30.5 0 15.8 10.6 29 24.8 33.5v92.2c-81.9-32.2-139.8-112-139.8-205.4 0-83.1 46-155.5 113.9-193.2 5.4-3 7.4-9.6 4.7-15.1-2.9-5.9-10.1-8.2-15.9-5-75 41.5-125.8 121.5-125.8 213.3 0 114.7 79.2 210.8 185.9 236.8v-104c7.6 2.5 15.1 4.6 23 6.2v123.7C131.4 465.2 31 354.1 31 219.5c0-32.8 6-64.3 16.9-93.3 2.2-5.8-.6-12.2-6.3-14.6-6-2.6-13 .4-15.3 6.6C14.5 149.7 8 183.8 8 219.5c0 155.1 122.6 281.6 276.3 287.8V361.4c6.8.4 15 .5 23.4 0v145.8C461.4 501.1 584 374.6 584 219.5c0-35.7-6.5-69.8-18.3-101.4zM365.9 275.5c13 0 23.7 10.5 23.7 23.7 0 13.1-10.6 23.7-23.7 23.7-13 0-23.7-10.5-23.7-23.7 0-13.1 10.6-23.7 23.7-23.7zm-139.8 47.3c-13.2 0-23.7-10.7-23.7-23.7s10.5-23.7 23.7-23.7c13.1 0 23.7 10.6 23.7 23.7 0 13-10.5 23.7-23.7 23.7z"/></svg>');}
    .fa-bitbucket {mask-image: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M22.2 32A16 16 0 0 0 6 47.8a26.35 26.35 0 0 0 .2 2.8l67.9 412.1a21.77 21.77 0 0 0 21.3 18.2h325.7a16 16 0 0 0 16-13.4L505 50.7a16 16 0 0 0-13.2-18.3 24.58 24.58 0 0 0-2.8-.2L22.2 32zm285.9 297.8h-104l-28.1-147h157.3l-25.2 147z"/></svg>');}
    </style>

.. role:: inline-icon
.. role:: eye
.. role:: eye-outline
.. role:: lightbulb
.. role:: lightbulb-outline
.. role:: sunny
.. role:: night
.. role:: toggle-off
.. role:: toggle-on
.. role:: fa-git
.. role:: fa-git-alt
.. role:: fa-git-square
.. role:: fa-github
.. role:: fa-github-alt
.. role:: fa-github-square
.. role:: fa-gitlab
.. role:: fa-gitkraken
.. role:: fa-bitbucket

.. |eye| image:: _static/images/blank.png
    :class: inline-icon eye

.. |eye-outline| image:: _static/images/blank.png
    :class: inline-icon eye-outline

.. |lightbulb| image:: _static/images/blank.png
    :class: inline-icon lightbulb

.. |lightbulb-outline| image:: _static/images/blank.png
    :class: inline-icon lightbulb-outline

.. |sunny| image:: _static/images/blank.png
    :class: inline-icon sunny

.. |night| image:: _static/images/blank.png
    :class: inline-icon night

.. |toggle-off| image:: _static/images/blank.png
    :class: inline-icon toggle-off

.. |toggle-on| image:: _static/images/blank.png
    :class: inline-icon toggle-on

.. |fa-git| image:: _static/images/blank.png
    :class: inline-icon fa-git
.. |fa-git-alt| image:: _static/images/blank.png
    :class: inline-icon fa-git-alt
.. |fa-git-square| image:: _static/images/blank.png
    :class: inline-icon fa-git-square
.. |fa-github| image:: _static/images/blank.png
    :class: inline-icon fa-github
.. |fa-github-alt| image:: _static/images/blank.png
    :class: inline-icon fa-github-alt
.. |fa-github-square| image:: _static/images/blank.png
    :class: inline-icon fa-github-square
.. |fa-gitlab| image:: _static/images/blank.png
    :class: inline-icon fa-gitlab
.. |fa-gitkraken| image:: _static/images/blank.png
    :class: inline-icon fa-gitkraken
.. |fa-bitbucket| image:: _static/images/blank.png
    :class: inline-icon fa-bitbucket

.. custom roles used to add a class to individual html elements
.. role:: red
.. role:: pink
.. role:: purple
.. role:: deep-purple
.. role:: indigo
.. role:: blue
.. role:: light-blue
.. role:: cyan
.. role:: teal
.. role:: green
.. role:: light-green
.. role:: lime
.. role:: yellow
.. role:: amber
.. role:: orange
.. role:: deep-orange
.. role:: brown
.. role:: grey
.. role:: blue-grey
.. role:: white
.. role:: black
.. role:: accent-red
.. role:: accent-pink
.. role:: accent-purple
.. role:: accent-deep-purple
.. role:: accent-indigo
.. role:: accent-blue
.. role:: accent-light-blue
.. role:: accent-cyan
.. role:: accent-teal
.. role:: accent-green
.. role:: accent-light-green
.. role:: accent-lime
.. role:: accent-yellow
.. role:: accent-amber
.. role:: accent-orange
.. role:: accent-deep-orange
.. role:: accent-brown
.. role:: accent-grey
.. role:: accent-blue-grey
.. role:: accent-white

.. custom styles used to demonstrate pallet & accent colors (only for this page)
.. raw:: html

    <style>
    .red {background-color:#ef5552; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .pink {background-color:#e92063; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .purple {background-color:#ab47bd; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .deep-purple {background-color:#7e56c2; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .indigo {background-color:#4051b5; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .blue {background-color:#2094f3; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .light-blue {background-color:#02a6f2; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .cyan {background-color:#00bdd6; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .teal {background-color:#009485; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .green {background-color:#4cae4f; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .light-green {background-color:#8bc34b; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .lime {background-color:#cbdc38; color:var(--md-code-bg-color); padding:0.05rem 0.3rem}
    .yellow {background-color:#ffec3d; color:var(--md-code-bg-color); padding:0.05rem 0.3rem}
    .amber {background-color:#ffc105; color:var(--md-code-bg-color); padding:0.05rem 0.3rem}
    .orange {background-color:#ffa724; color:var(--md-code-bg-color); padding:0.05rem 0.3rem}
    .deep-orange {background-color:#ff6e42; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .brown {background-color:#795649; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .grey {background-color:#757575; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .blue-grey {background-color:#546d78; color:var(--md-code-fg-color); padding:0.05rem 0.3rem}
    .white {background-color:#fff; color:#000; padding:0.05rem 0.3rem}
    .black {background-color:#000; color:#fff; padding:0.05rem 0.3rem}

    .accent-red {color:#ef5552; background-color:var(--md-code-bg-color)}
    .accent-pink {color:#e92063; background-color:var(--md-code-bg-color)}
    .accent-purple {color:#ab47bd; background-color:var(--md-code-bg-color)}
    .accent-deep-purple {color:#7e56c2; background-color:var(--md-code-bg-color)}
    .accent-indigo {color:#4051b5; background-color:var(--md-code-bg-color)}
    .accent-blue {color:#2094f3; background-color:var(--md-code-bg-color)}
    .accent-light-blue {color:#02a6f2; background-color:var(--md-code-bg-color)}
    .accent-cyan {color:#00bdd6; background-color:var(--md-code-bg-color)}
    .accent-teal {color:#009485; background-color:var(--md-code-bg-color)}
    .accent-green {color:#4cae4f; background-color:var(--md-code-bg-color)}
    .accent-light-green {color:#8bc34b; background-color:var(--md-code-bg-color)}
    .accent-lime {color:#cbdc38; background-color:var(--md-code-bg-color)}
    .accent-yellow {color:#ffec3d; background-color:var(--md-code-bg-color)}
    .accent-amber {color:#ffc105; background-color:var(--md-code-bg-color)}
    .accent-orange {color:#ffa724; background-color:var(--md-code-bg-color)}
    .accent-deep-orange {color:#ff6e42; background-color:var(--md-code-bg-color)}
    </style>

.. _customization:

=============
Customization
=============

There are two methods to alter the theme.  The first, and simplest, uses the
options exposed through ``html_theme_options`` in ``conf.py``. This site's
options are:

.. code-block:: python

    html_theme_options = {
        'site_url': 'http://bashtage.github.io/sphinx-material/',
        'repo_url': 'https://github.com/bashtage/sphinx-material/',
        'repo_name': 'Material for Sphinx',
        'google_analytics': ['UA-XXXXX','auto'],
        'html_minify': True,
        'globaltoc_depth': 2
    }

Heroes
==========

To set the hero's text for an individual page, use the ``:hero:`` directive for the desired page.
If not specified, then the page will not have a hero section.

Configuration Options
=====================

``html_logo``
**************

The logo in the navigation side menu and header (when browser viewport is wide enough) is changed
by specifying the ``html_logo`` option. This must specify an image in the project's path
(typically in the *docs/images* folder).

``html_theme_options`` dict
****************************

``site_url``
------------

Specify a site_url used to generate sitemap.xml links. If not specified, then
no sitemap will be built.

``repo_url``
------------

Set the repo url for the link to appear.

``repo_name``
-------------

The name of the repo. If must be set if repo_url is set.

``repo_type``
-------------

Must be one of github, gitlab or bitbucket.

``edit_uri``
-------------

This is the url segment that is concatenated with repo_url to point readers to the document's
source file. This is typically in the form of ``'blob/<branch name>/<docs source folder>'``.
Defaults to a blank string (which disables the edit icon). This is disabled for builds on
ReadTheDocs as they implement their own mechanism based on the repository's branch or tagged
commit.

``features``
------------

Some features that have been ported and can be enabled by specifying the features name in a list
of strings. The following features are supported:

- `navigation.expand <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-expansion>`_
- `navigation.tabs <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-tabs>`_ (only shows for browsers with large viewports)
- `toc.integrate <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-integration>`_
- `navigation.sections <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-sections>`_
- `navigation.instant <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading>`_
- `header.autohide <https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-header/#automatic-hiding>`_
- `navigation.top <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#back-to-top-button>`_
- `search.highlight <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-highlighting>`_
- `search.share <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-sharing>`_

``icon`` for the repository
---------------------------

The icon that represents the source code repository can be changed using the ``repo`` field of the
``icon`` `dict` (within the ``html_theme_options`` `dict`). Although this icon can be
`any of the icons bundled with this theme <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_,
popular choices are:

- |fa-git| ``fontawesome/brands/git``
- |fa-git-alt| ``fontawesome/brands/git-alt``
- |fa-git-square| ``fontawesome/brands/git-square``
- |fa-github| ``fontawesome/brands/github``
- |fa-github-alt| ``fontawesome/brands/github-alt``
- |fa-github-square| ``fontawesome/brands/github-square``
- |fa-gitlab| ``fontawesome/brands/gitlab``
- |fa-gitkraken| ``fontawesome/brands/gitkraken``
- |fa-bitbucket| ``fontawesome/brands/bitbucket``

``palette``
-----------

The theme's color pallet. This theme requires at least 2 schemes specified (ie 1
scheme for light & 1 scheme for dark). Each scheme needs a specified ``primary`` and
``accent`` colors. Additionally, each scheme must have a ``toggle`` `dict` in which
the ``name`` field specifies the text in the tooltip and the ``icon`` field specifies
an icon to use to visually indicate which scheme is currently used.

- ``primary`` color

  Options are

  :red:`red`, :pink:`pink`, :purple:`purple`, :deep-purple:`deep-purple`, :indigo:`indigo`, :blue:`blue`,
  :light-blue:`light-blue`, :cyan:`cyan`, :teal:`teal`, :green:`green`, :light-green:`light-green`,
  :lime:`lime`, :yellow:`yellow`, :amber:`amber`, :orange:`orange`, :deep-orange:`deep-orange`,
  :brown:`brown`, :grey:`grey`, :blue-grey:`blue-grey`, :black:`black`, and :white:`white`.
- ``accent`` color

  Options are

  :accent-red:`red`, :accent-pink:`pink`, :accent-purple:`purple`, :accent-deep-purple:`deep-purple`,
  :accent-indigo:`indigo`, :accent-blue:`blue`, :accent-light-blue:`light-blue`, :accent-cyan:`cyan`,
  :accent-teal:`teal`, :accent-green:`green`, :accent-light-green:`light-green`, :accent-lime:`lime`,
  :accent-yellow:`yellow`, :accent-amber:`amber`, :accent-orange:`orange`, :accent-deep-orange:`deep-orange`.
- Toggle ``icon``

  Options must be `any of the icons bundled with this theme <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_.
  Popular combinations are

  .. csv-table::

      |toggle-off| ``material/toggle-switch-off-outline``, |toggle-on| ``material/toggle-switch``
      |sunny| ``material/weather-sunny``, |night| ``material/weather-night``
      |eye-outline| ``material/eye-outline``, |eye| ``material/eye``
      |lightbulb-outline| ``material/lightbulb-outline``, |lightbulb| ``material/lightbulb``

``direction``
---------------

Specifies the text direction.  Set to ``ltr`` (default) for left-to-right,
or ``rtl`` for right-to-left.

``google_analytics_account``
----------------------------

Set to enable google analytics.
``globaltoc_depth``
-------------------

The maximum depth of the global TOC; set it to -1 to allow unlimited depth.

``globaltoc_collapse``
----------------------

If true, TOC entries that are not ancestors of the current page are collapsed.

``globaltoc_includehidden``
---------------------------

If true, the global TOC tree will also contain hidden entries.

``version_dropdown``
---------------------------

A flag indicating whether the version drop down should be included. You must supply a JSON file
to use this feature.

``version_dropdown_text``
---------------------------

The text in the version dropdown button

``version_json``
---------------------------

The location of the JSON file that contains the version information. The default assumes there
is a file versions.json located in the root of the site.

``version_info``
---------------------------

A dictionary used to populate the version dropdown.  If this variable is provided, the static
dropdown is used and any JavaScript information is ignored.

Customizing the layout
======================

You can customize the theme by overriding Jinja template blocks. For example,
"layout.html" contains several blocks that can be overridden or extended.

Place a "layout.html" file in your project's "/_templates" directory (typically located in the
"docs" directory).

.. code-block:: bash

    mkdir source/_templates
    touch source/_templates/layout.html

Then, configure your 'conf.py':

.. code-block:: python

    templates_path = ['_templates']

Finally, edit your override file ``source/_templates/layout.html``:

.. code-block:: jinja

    {# Import the theme's layout. #}
    {% extends '!layout.html' %}

    {%- block extrahead %}
    {# Add custom things to the head HTML tag #}
    {# Call the parent block #}
    {{ super() }}
    {%- endblock %}

New Blocks
==========
The theme has a small number of new blocks to simplify some types of
customization:

``footerrel``
    Previous and next in the footer.
``font``
    The default font inline CSS and the class to the google API. Use this
    block when changing the font.
``fonticon``
    Block that contains the icon font. Use this to add additional icon fonts
    (e.g., `FontAwesome <https://fontawesome.com/>`_). You should probably call ``{{ super() }}`` at
    the end of the block to include the default icon font as well.

Version Dropdown
================

A version dropdown is available that lets you store multiple versions in a single site.
The standard structure of the site, relative to the base is usually::

    /
    /devel
    /v1.0.0
    /v1.1.0
    /v1.1.1
    /v1.2.0


To use the version dropdown, you must set ``version_dropdown`` to ``True`` in
the sites configuration.

There are two approaches, one which stores the version information in a JavaScript file
and one which uses a dictionary in the configuration.

Using a Javascript File
*************************

The data used is read via javascript from a file. The basic structure of the file is a dictionary
of the form [label, path].

.. code-block::javascript

    {
        "release": "",
        "development": "devel",
        "v1.0.0": "v1.0.0",
        "v1.1.0": "v1.1.0",
        "v1.1.1": "v1.1.0",
        "v1.2.0": "v1.2.0",
    }

This dictionary tells the dropdown that the release version is in the root of the site, the
other versions are archived under their version number, and the development version is
located in /devel.

.. note::

    The advantage of this approach is that you can separate version information
    from the rendered documentation.  This makes is easy to change the version
    dropdown in _older_ versions of the documentation to reflect additional versions
    that are released later. Changing the Javascript file changes the version dropdown
    content in all versions.  This approach is used in
    `statsmodels <https://www.statsmodels.org/>`_.

Using ``conf.py``
-----------------

.. warning::

    This method has precedence over the JavaScript approach. If ``version_info`` is
    not empty in a site's ``html_theme_options``, then the static approach is used.

The alternative uses a dictionary where the key is the title and the value is the target.
The dictionary is part of the size configuration's ``html_theme_options``.

.. code-block::python

    "version_info": {
        "release": "",  # empty is the master doc
        "development": "devel/",
        "v1.0.0": "v1.0.0/",
        "v1.1.0": "v1.1.0/",
        "v1.1.1": "v1.1.0/",
        "v1.2.0": "v1.2.0/",
        "Read The Docs": "https://rtd.readthedocs.io/",
    }

The dictionary structure is nearly identical.  Here you can use relative paths
like in the JavaScript version. You can also use absolute paths.

.. note::

    This approach is easier if you only want to have a fixed set of documentation,
    e.g., stable and devel.
