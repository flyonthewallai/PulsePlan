import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

if (!OPENAI_API_KEY) {
  console.error('OpenAI API key not found in environment variables');
  process.exit(1);
}

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: OPENAI_API_KEY
});

export default openai; 