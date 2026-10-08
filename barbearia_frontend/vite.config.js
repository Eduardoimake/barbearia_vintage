import { defineConfig, loadEnv } from 'vite';

/**
 * Configuração do Vite.
 * O proxy encaminha /api e /media ao Django, mantendo tudo na mesma origem.
 * Assim o cookie de sessão e o CSRF funcionam sem configurar CORS.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const alvo = env.VITE_PROXY_TARGET || 'http://localhost:8000';

  return {
    server: {
      port: 5173,
      proxy: {
        // changeOrigin=false preserva o Host/Origin do navegador (validação CSRF do Django)
        '/api': { target: alvo, changeOrigin: false },
        '/media': { target: alvo, changeOrigin: false },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  };
});