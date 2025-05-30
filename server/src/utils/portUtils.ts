import { createServer } from 'http';

/**
 * Check if a specific port is available
 */
export async function isPortAvailable(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = createServer();
    
    server.listen(port, () => {
      server.close(() => {
        resolve(true);
      });
    });

    server.on('error', () => {
      resolve(false);
    });
  });
}

/**
 * Find the next available port starting from a given port
 */
export async function findAvailablePort(startPort: number, maxAttempts: number = 10): Promise<number> {
  return new Promise((resolve, reject) => {
    let attempts = 0;

    async function tryPort(port: number) {
      if (attempts >= maxAttempts) {
        reject(new Error(`Unable to find available port after ${maxAttempts} attempts starting from ${startPort}`));
        return;
      }

      const available = await isPortAvailable(port);
      
      if (available) {
        resolve(port);
      } else {
        console.log(`⚠️  Port ${port} is already in use, trying port ${port + 1}...`);
        attempts++;
        await tryPort(port + 1);
      }
    }

    console.log(`🔍 Checking if port ${startPort} is available...`);
    tryPort(startPort);
  });
}

/**
 * Get a list of common ports to try for development
 */
export function getCommonPorts(basePort: number = 5000): number[] {
  return [
    basePort,      // 5000
    basePort + 1,  // 5001
    basePort + 2,  // 5002
    basePort + 3,  // 5003
    3000,          // Common React port
    3001,          // Common alternative
    8000,          // Common backend port
    8080,          // Common alternative
    9000,          // Another common option
  ];
} 