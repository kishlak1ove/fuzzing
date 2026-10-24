const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const url = process.argv[2];
  const out = process.argv[3] || '/results/puppeteer.json';

  const browser = await puppeteer.launch({
    headless: 'shell',                                      // ← было 'new'
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',                            // ← добавлено
      '--disable-gpu',                                      // ← добавлено
      '--single-process',                                   // ← добавлено
      '--no-zygote',                                        // ← добавлено
      '--disable-features=IsolateOrigins,site-per-process', // ← добавлено
    ],
    timeout: 60000,                                          // ← было 30000
  });

  const page = await browser.newPage();

  const xhr = [];
  page.on('request', r => {
    const u = r.url();
    const t = r.resourceType();
    if ((t === 'xhr' || t === 'fetch') && !/\.(js|css|png|jpg|svg|woff|ico|map)$/i.test(u)) {
      xhr.push({ url: u, method: r.method() });
    }
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
    const forms = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('input,textarea,select,form').forEach(el => {
        out.push({
          tag: el.tagName,
          name: el.name || '',
          id: el.id || '',
          type: el.type || '',
          placeholder: el.placeholder || '',
        });
      });
      return out;
    });
    fs.writeFileSync(out, JSON.stringify({ url, xhr, forms }, null, 2));
    console.log(`XHR: ${xhr.length}, Forms: ${forms.length}`);
  } catch (e) {
    console.error('Error:', e.message);
    fs.writeFileSync(out, JSON.stringify({ error: e.message }));
  } finally {
    await browser.close();
  }
})(); 