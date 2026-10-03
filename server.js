require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.NODE_PORT || 5000;

app.use(cors());
app.use(express.json({ limit: '20mb' }));
app.use('/static', express.static(path.join(__dirname, 'static')));

// Hugging Face Image Generation Route
app.post('/api/generate-image-hf', async (req, res) => {
  const { prompt, model = 'black-forest-labs/FLUX.1-dev' } = req.body;
  const hfToken = process.env.HF_TOKEN || process.env.HUGGINGFACE_API_KEY;

  if (!hfToken) {
    return res.status(400).json({ error: 'HF_TOKEN is not configured in .env' });
  }

  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`https://router.huggingface.co/hf-inference/models/${model}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ inputs: prompt })
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(response.status).json({ error: errText });
    }

    const buffer = await response.buffer();
    const filename = `panel_${Date.now()}.png`;
    const filePath = path.join(__dirname, 'static', 'panels', filename);
    fs.writeFileSync(filePath, buffer);

    return res.json({
      success: true,
      image_path: `/static/panels/${filename}`
    });
  } catch (err) {
    console.error('HF Generation Error:', err);
    return res.status(500).json({ error: err.message });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'ComicCraft HF Node Service' });
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Express HF Server running on port ${PORT}`);
  });
}

module.exports = app;
