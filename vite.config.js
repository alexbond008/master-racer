// The game uses top-level await (data loading before the world is built), so target modern browsers.
export default { build: { target: 'esnext', chunkSizeWarningLimit: 4000 } };
