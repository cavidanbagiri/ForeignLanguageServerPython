# Talqo Backend - Cloud Run-a Deploy

## 0) Ehtiyat tədbiri - xərci məhdudlaşdır

Google Cloud Console-da (deploy etməzdən əvvəl belə):
1. **Billing** → **Budgets & alerts** → yeni büdcə yarat, məs. **$5** limit qoy, e-poçt xəbərdarlığı aktivləşdir.
2. Bu, kartına gözlənilməz məbləğ düşməsinin qarşısını alan ilk sığortadır.

## 1) gcloud CLI quraşdır

https://cloud.google.com/sdk/docs/install ünvanından öz OS-ə uyğun quraşdırıcını yüklə.

Quraşdırdıqdan sonra:
```bash
gcloud init
gcloud auth login
```
Bu zaman brauzerdə Google hesabınla daxil olacaqsan və layihə (project) yaradacaqsan/seçəcəksən.

## 2) Lazımi API-ləri aktivləşdir

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com texttospeech.googleapis.com
```

(`texttospeech.googleapis.com` - səsləndirmə funksiyası üçün lazımdır)

## 3) Backend qovluğuna keç və deploy et

```bash
cd backend
gcloud run deploy talqo-backend \
  --source . \
  --region me-west1 \
  --allow-unauthenticated \
  --max-instances 2 \
  --memory 512Mi \
  --set-env-vars GEMINI_API_KEY=sk-of-sənin-açarın,GEMINI_MODEL=google/gemini-3.8-flash,GEMINI_BASE_URL=https://api.ofox.ai/gemini
```

Nələr baş verir:
- `--source .` → Dockerfile-ı tapıb konteyneri Google-un buludunda avtomatik qurur (sənin kompüterində Docker quraşdırmağa ehtiyac yoxdur)
- `--region me-west1` → **Tier 1** (pulsuz tier işləyir) və Bakıya coğrafi olaraq ən yaxın belə region
- `--allow-unauthenticated` → mobil tətbiq açar/token olmadan çağıra bilsin deyə (öz backend-imizdir, ictimai API)
- `--max-instances 2` → sürpriz hesab riskindən əlavə qorunma
- `--set-env-vars` → `.env` faylının yerini tutur - **`.env` Docker image-ə daxil edilmir** (`.dockerignore`-da xaric etmişik), açarlar birbaşa Cloud Run-un öz mühitinə yazılır

İlk dəfə bir neçə dəqiqə çəkə bilər (build + deploy). Bitəndə terminalda belə bir sətir görəcəksən:
```
Service URL: https://talqo-backend-xxxxxxxxxx.me-west1.run.app
```
**Bu URL-i saxla** - bu, sənin yeni backend ünvanındır, HTTPS ilə, hazırdan işlək.

## 4) Test et

```bash
curl https://talqo-backend-xxxxxxxxxx.me-west1.run.app/health
```
`{"status":"ok"}` gəlməlidir.

## 5) Frontend-i yeni ünvana yönləndir

`config/api.js`:
```javascript
export const API_BASE_URL = 'https://talqo-backend-xxxxxxxxxx.me-west1.run.app';
```

İndi artıq eyni Wi-Fi/hotspot lazım deyil - telefon istənilən şəbəkədən (mobil data daxil) backend-ə çata bilər.

## 6) Kod dəyişəndə yenidən deploy

Backend kodunda dəyişiklik edəndə eyni əmri təkrar işə sal:
```bash
cd backend
gcloud run deploy talqo-backend --source . --region me-west1
```
(env dəyişənlərini təkrar yazmağa ehtiyac yoxdur, saxlanılır - yalnız dəyişdirmək istəsən `--set-env-vars`-ı yenidən ver)

## Xərc gözləntisi

Sənin hazırkı test miqyasında (bir neçə istifadəçi, gündə bir neçə onlarla sorğu) demək olar **$0** qalmalıdır - pulsuz tier (ayda 2 milyon sorğu, 180,000 vCPU-saniyə) bu qədər trafiki asanlıqla qarşılayır. Kartındakı $10 hətta pulsuz tier bitsə belə uzun müddət kifayət edər.
