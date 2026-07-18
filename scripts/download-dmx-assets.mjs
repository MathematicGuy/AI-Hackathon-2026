import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const root = process.cwd();

const assets = [
  ["images/chatbot/chat-bot.png", "https://cdnv2.tgdd.vn/webmwg/devops/prod/chat-bot-dmx/icons/dmx/chat-bot.png"],
  ["images/chatbot/mascot.png", "https://cdnv2.tgdd.vn/webmwg/devops/prod/chat-bot-dmx/icons/dmx/mascot.png"],
  ["images/flashsale/campaign-background.jpg", "https://cdnv2.tgdd.vn/mwg-static/common/Campaign/de/95/de956ecb3e56aa9d649d40c3b6dcfa05.jpg"],
  ["images/flashsale/game-banner.png", "https://cdnv2.tgdd.vn/mwg-static/common/Campaign/a0/13/a013f6f6b1549c4395dc476c8c165017.png"],
  ["images/flashsale/wheel-banner.gif", "https://cdnv2.tgdd.vn/mwg-static/common/Campaign/52/9f/529feb405475012d6c7d323774852552.gif"],
  ["images/flashsale/deal-title.png", "https://cdnv2.tgdd.vn/mwg-static/common/Campaign/ca/b4/cab449ed44558f18044c443462ef7371.png"],
  ["images/menu/hot-flash-sale.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/70/6d/706d8c2e4e66339775b17916d4348cb0.png"],
  ["images/menu/hot-online-only.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/8d/01/8d0134fde58957b6efda4fba17c509c7.png"],
  ["images/menu/hot-cool-station.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/c9/1b/c91bcfdb99fc0f3b2e2ebefc4903f28f.png"],
  ["images/menu/hot-blender.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/c6/31/c631b2d23911b8ace515d2c8d75d4f33.png"],
  ["images/menu/hot-water-filter.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/e2/95/e2956ca2497ad19984644b9bb0712020.png"],
  ["images/menu/hot-aqua-haier.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/fd/a5/fda5c4ccf30fe861d476d129237dbf1b.png"],
  ["images/menu/hot-clearance.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/9e/97/9e971eea7180a1a98224ae8a729ba8ab.png"],
  ["images/menu/hot-water-dispenser.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/a3/eb/a3ebc13c7c0c3e53ae8535864c978400.png"],
  ["images/menu/hot-hand-tools.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/b7/f6/b7f6cf849afc93b36f8e75b5bf4a4d5a.png"],
  ["images/menu/hot-stove.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/a2/6a/a26a96f8397e844996ffd2343c5812e7.png"],
  ["images/menu/hot-rice-cooker.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/98/2c/982caf4f843d4fffc04be83bc21ea9e7.png"],
  ["images/menu/hot-fridge.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/8a/05/8a054804cdc69512d479a636758fad5f.png"],
  ["images/menu/hot-large-tv.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/da/96/da96060fed5721776d032ea2edf1d18d.png"],
  ["images/menu/hot-health-beauty.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/de/c8/dec84954f7032ab0a8eb3432641b6838.png"],
  ["images/menu/hot-kitchen.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/58/c3/58c3af05bcf7978c4028d617a0f53f61.png"],
  ["images/menu/hot-installation.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/fc/94/fc94ec9b9b582b2aca5de2f834e8031a.png"],
  ["images/menu/hot-dehumidifier.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/9d/da/9ddafd366770d67f0efdc8a82f706ee3.png"],
  ["images/menu/hot-premium.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/1c/ac/1cacbacf2f23ae1341ad05b39f8e6eb8.png"],
  ["images/menu/hot-camera.jpg", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/3d/b0/3db0fd5582c9ba88787469b4910bf0ec.jpg"],
  ["images/menu/hot-solar-light.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/e9/89/e989553af85fcbe7fb59b6b6f07701f7.png"],
  ["images/menu/info-buying-advice.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/80/2c/802cd9f7fde94d34c52b4ec1713f4a39.png"],
  ["images/menu/info-promotions.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/87/9e/879e8a9d7e88268da1c39cdb92f06ed0.png"],
  ["images/menu/info-stores.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/ff/48/ff4824ab538d79fcdf763ad8c631caaa.png"],
  ["images/menu/info-installments.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/09/a8/09a8d501ac138519c8e9319b594ddee1.png"],
  ["images/menu/info-warranty.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/3c/51/3c51a9150cd4e1f2ce5dd5de59bfc9f7.png"],
  ["images/menu/service-clean-ac.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/33/44/33441287a16a42605737804b5b88551d.png"],
  ["images/menu/service-replace-filter.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/92/9a/929a8baf481c1460f07522cc1dd2ba31.png"],
  ["images/menu/service-clean-washer.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/12/4b/124b1e1fbe78990ab9c0147805b31260.png"],
  ["images/menu/service-vehicle-insurance.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/5e/79/5e79d261170994eb2d947688fee846c5.png"],
  ["images/menu/service-sim-card.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/5c/d8/5cd8ad6a60d9fadd882225eb99a79456.png"],
  ["images/menu/service-pay-installment.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/5f/58/5f58037c859443ab9b224a9b8900d353.png"],
  ["images/menu/service-online-grocery.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/e3/11/e311bfd61d1dfd9ca8714e12c1883e88.png"],
  ["images/menu/service-cake.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/6f/0a/6f0a96e0a16c49fd07d0718042e5ec34.png"],
  ["images/menu/service-cathay.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/8e/dd/8edd4e869e65430df90bb1615e0d2cfc.png"],
  ["images/menu/service-flight.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/7e/ba/7eba2d02f5ca3140453eecb1517fb090.png"],
  ["images/menu/service-kredivo.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/73/40/7340f2f78399b4c8f64f35dafceca590.png"],
  ["images/menu/service-evomoney.png", "https://cdnv2.tgdd.vn/mwg-static/dmx/Common/84/92/8492d5538d8f2ce5b88267b2c46ee9c5.png"],
];

async function download([relativePath, url]) {
  const destination = join(root, "public", relativePath);
  await mkdir(dirname(destination), { recursive: true });
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${url}`);
  }
  await writeFile(destination, Buffer.from(await response.arrayBuffer()));
  return relativePath;
}

const concurrency = 6;
for (let index = 0; index < assets.length; index += concurrency) {
  const batch = assets.slice(index, index + concurrency);
  const downloaded = await Promise.all(batch.map(download));
  process.stdout.write(`${downloaded.join("\n")}\n`);
}

process.stdout.write(`Downloaded ${assets.length} assets.\n`);
