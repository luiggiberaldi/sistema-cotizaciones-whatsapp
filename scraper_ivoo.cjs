const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');

const uuid = () => crypto.randomUUID();

// Función auxiliar para descargar imagen URL -> Base64
const urlToBase64 = (url) => {
    return new Promise((resolve, reject) => {
        if (!url || !url.startsWith('http')) { resolve(null); return; }

        https.get(url, (res) => {
            if (res.statusCode !== 200) { resolve(null); return; }
            const chunks = [];
            res.on('data', d => chunks.push(d));
            res.on('end', () => {
                const buffer = Buffer.concat(chunks);
                const type = res.headers['content-type'] || 'image/jpeg';
                resolve(`data:${type};base64,${buffer.toString('base64')}`);
            });
            res.on('error', (e) => resolve(null));
        }).on('error', (e) => resolve(null));
    });
};

(async () => {
    console.log('🕷️ Iniciando Scraper IVOO...');

    const MAX_RETRIES = 3;
    let browser = null;

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
            console.log(`🕷️ Iniciando Scraper IVOO (Intento ${attempt}/${MAX_RETRIES})...`);

            browser = await puppeteer.launch({
                headless: "new",
                defaultViewport: { width: 1366, height: 768 },
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
            const page = await browser.newPage();
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

            console.log('🌐 Navegando a https://www.ivoo.com/ ...');
            await page.goto('https://www.ivoo.com/', { waitUntil: 'networkidle2', timeout: 90000 });

            console.log('📜 Haciendo scroll para cargar productos...');
            await page.evaluate(async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 400;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= 5000 || totalHeight >= scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 150);
                });
            });

            await new Promise(r => setTimeout(r, 4000));

            console.log('⛏️ Extrayendo productos...');

            const extractedData = await page.evaluate(() => {
                const products = [];
                const seenImages = new Set();
                const images = Array.from(document.querySelectorAll('img')).filter(img =>
                    img.width > 150 && img.height > 150 && img.src.startsWith('http')
                );

                images.forEach(img => {
                    if (seenImages.has(img.src)) return;
                    let container = img.parentElement;
                    let foundName = null;
                    let foundPrice = null;

                    for (let i = 0; i < 7; i++) {
                        if (!container) break;
                        const text = container.innerText;
                        if (!text) { container = container.parentElement; continue; }
                        const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 1);

                        const priceLines = lines.filter(l =>
                            (l.includes('$') || l.includes('USD')) &&
                            /[\d.,]+/.test(l)
                        );

                        if (priceLines.length > 0) {
                            const cleanPrices = priceLines.map(l => {
                                const clean = l.replace(/[^\d.,]/g, '');
                                const lastDot = clean.lastIndexOf('.');
                                const lastComma = clean.lastIndexOf(',');
                                const lastSeparator = Math.max(lastDot, lastComma);
                                if (lastSeparator === -1) return parseFloat(clean) || 0;
                                const integerPart = clean.slice(0, lastSeparator).replace(/[.,]/g, '');
                                const decimalPart = clean.slice(lastSeparator + 1);
                                if (decimalPart.length > 2) {
                                    return parseFloat(clean.replace(/[.,]/g, '')) / (10 ** decimalPart.length);
                                }
                                return parseFloat(`${integerPart}.${decimalPart}`) || 0;
                            }).filter(p => p > 0);
                            if (cleanPrices.length > 0) foundPrice = Math.max(...cleanPrices);
                        }

                        const potentialNames = lines.filter(l =>
                            !l.includes('$') &&
                            !l.toLowerCase().includes('usd') &&
                            !l.toLowerCase().includes('iva') &&
                            !l.toLowerCase().includes('envío') &&
                            l.length > 12 &&
                            l.length < 120
                        );

                        if (potentialNames.length > 0 && !foundName) {
                            foundName = potentialNames[0];
                        }
                        if (foundName && foundPrice) break;
                        container = container.parentElement;
                    }

                    if (foundName && foundPrice) {
                        products.push({
                            name: foundName,
                            src: img.src,
                            price: foundPrice
                        });
                        seenImages.add(img.src);
                    }
                });
                return products;
            });

            if (!extractedData || extractedData.length === 0) {
                // Si falla en encontrar productos, lanzar error para reintento
                throw new Error("No se encontraron productos en el DOM.");
            }

            console.log(`✅ Detectados ${extractedData.length} productos.`);

            const generatedProducts = [];
            let count = 0;

            for (const p of extractedData) {
                if (p.price >= 200 || p.price < 10) continue;
                if (count >= 50) break;
                let cleanName = p.name.trim().toLowerCase().replace(/\s+/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                console.log(`📥 [${count + 1}] ${cleanName.slice(0, 30)}... ($${p.price.toFixed(2)})`);

                const base64 = await urlToBase64(p.src);
                if (base64) {
                    generatedProducts.push({
                        id: uuid(),
                        name: cleanName,
                        priceUsdt: p.price,
                        image: base64,
                        createdAt: new Date().toISOString()
                    });
                    count++;
                }
            }

            if (generatedProducts.length > 0) {
                const backupData = {
                    timestamp: new Date().toISOString(),
                    version: "1.0",
                    data: { my_products_v1: JSON.stringify(generatedProducts) }
                };
                const outputPath = path.join(__dirname, 'backup_ivoo.json');
                fs.writeFileSync(outputPath, JSON.stringify(backupData, null, 2));
                console.log(`\n🎉 Backup generado: ${outputPath}`);
                console.log(`Total productos: ${generatedProducts.length}`);
            }

            break; // Éxito

        } catch (e) {
            console.error(`❌ Intento ${attempt} fallido:`, e.message);
            if (attempt === MAX_RETRIES) console.error("❌ Fallo definitivo IVOO.");
            else await new Promise(r => setTimeout(r, 5000));
        } finally {
            if (browser) await browser.close();
        }
    }
})();
