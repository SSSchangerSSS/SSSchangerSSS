<div align="center">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="assets/banner-static.svg?v=1" />
    <img src="assets/banner.svg?v=3" width="100%" alt="بنر سبک ماتریکس: باران کد سبز پشت پنل ترمینال تیره با نام سهراب ایران‌پک — مهندس نرم‌افزار R&D" />
  </picture>
</div>

# سهراب ایران‌پک

[English](README.md) · **فارسی**

<div dir="rtl">

```bash
$ whoami
sohrab-iranpak — R&D Software Engineer

$ cat focus.txt
robotics & simulation · MATLAB · .NET (WPF/MVVM) · game development · web & mobile
```

میان شبیه‌سازی رباتیک، مهندسی دات‌نت و بازی‌سازی جابه‌جا می‌شوم — و دوست دارم کارها را تا انتها ببرم: یک شبیه‌ساز ربات در MATLAB با رابط کاربری واقعی، یک برنامهٔ کامل دسکتاپ با WPF/MVVM، و بازی‌هایی که همین حالا در مرورگر قابل بازی‌اند.

## ماتریکس مشارکت‌ها

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/SSSchangerSSS/SSSchangerSSS/output/github-contribution-grid-snake-dark.svg?v=5" />
    <img src="https://raw.githubusercontent.com/SSSchangerSSS/SSSchangerSSS/output/github-contribution-grid-snake.svg?v=5" alt="مار سبز ماتریکسی روی تقویم مشارکت‌های گیت‌هاب که خانه‌های دارای مشارکت را می‌خورد" />
  </picture>
</div>

یک مار سبز فسفری روی تقویم واقعی مشارکت‌های من. مسیرش را روی خانه‌هایی که واقعاً مشارکت دارند می‌گذراند و آن‌ها را می‌خورد — خانهٔ خورده‌شده تا شروع چرخهٔ بعدی خالی می‌ماند. انیمیشن هر روز توسط GitHub Actions بازتولید می‌شود (موتور: [Platane/snk](https://github.com/Platane/snk)، پالت ماتریکسی)؛ اگر دریافت داده شکست بخورد، انیمیشن روز قبل باقی می‌ماند و تقویم جعلی منتشر نمی‌شود.

## پروژه‌های منتخب

### ⚔️ [The Great Rostam](https://github.com/SSSchangerSSS/The-Great-Rostam)

بازی اکشن دوبعدیِ فریم‌به‌فریم با الهام از شاهنامهٔ فردوسی — رستم در برابر شیر، ساخته‌شده برای مرورگر.

- **فناوری:** HTML5 Canvas · جاوااسکریپت خالص (ES Modules) · لایهٔ رابط با CSS · صدای رویه‌ای با WebAudio (بدون فایل صوتی)
- **چه چیزی کار می‌کند:** انیمیشن فریم‌به‌فریم با شیت‌های نقاشی‌شدهٔ دستی (حدود ۲۰۰ فریم) قفل‌شده به ماشین حالت مبارزه، ضربهٔ نهایی به سبک God of War با QTE، صحرای پارالاکس چندلایه، کنترل لمسی موبایل‌محور با قفل ۶۰ فریم بر ثانیه
- ▶️ **قابل بازی در مرورگر:** [ssschangersss.github.io/The-Great-Rostam](https://ssschangersss.github.io/The-Great-Rostam/)

<img src="https://raw.githubusercontent.com/SSSchangerSSS/The-Great-Rostam/main/docs/screenshots/title.png" width="460" alt="صفحهٔ عنوان بازی The Great Rostam" />

### 🤖 [شبیه‌سازی ربات RRR](https://github.com/SSSchangerSSS/3degree_RRR_robot_in_matlab_genetic_algorithm)

شبیه‌سازی بازوی ربات سه‌درجه‌آزادی (RRR) در متلب بر بستر ابزار Peter Corke Robotics Toolbox، همراه با رابط کاربری دست‌ساز.

- **فناوری:** MATLAB · Robotics Toolbox پیتر کروک · رابط گرافیکی · الگوریتم ژنتیک
- **چه چیزی کار می‌کند:** سینماتیک مستقیم و معکوس با دو روش مستقل — ابزار کروک و پیاده‌سازی خودبومیِ ماتریس تبدیل + الگوریتم ژنتیک — که در همان رابط کاربری کنار هم محاسبه و با یکدیگر مقایسه می‌شوند؛ به‌همراه رسم سه‌بعدی، ویدیوی آموزشی و مراجع PDF

<img src="https://raw.githubusercontent.com/SSSchangerSSS/3degree_RRR_robot_in_matlab_genetic_algorithm/main/robot.PNG" width="460" alt="رابط گرافیکی شبیه‌ساز ربات RRR در متلب — نتایج ابزار و حل‌کنندهٔ شخصی کنار هم" />

### 🚗 [مدیریت اجارهٔ خودرو — WPF](https://github.com/SSSchangerSSS/MVVM_WPF_Car_Rental_Management_App)

یک برنامهٔ کامل ویندوزی برای عملیات اجارهٔ خودرو، ساخته‌شده با پایبندی سخت‌گیرانه به الگوی MVVM.

- **فناوری:** C# · WPF · MVVM · Entity Framework Core · SQLite · تزریق وابستگی با Microsoft.Extensions.Hosting · AutoMapper · Material Design
- **درون پروژه:** عملیات CRUD عمومی، کارخانهٔ ساخت ViewModel، ناوبری و ارتباط اصولی میان ViewModelها، دسترسی غیرهمگام به داده، و لایهٔ Store برای کاستن از رفت‌وبرگشت‌های اضافه به پایگاه داده

### 🎮 [بازی دوبعدی با LÖVE 2D](https://github.com/SSSchangerSSS/2d_lua_game_made_with_love2d_engine_for_android)

یک بازی کامل دوبعدی به زبان Lua با موتور LÖVE 2D و بسته‌بندی‌شده برای اندروید.

- **فناوری:** Lua · LÖVE 2D · بستهٔ اندروید (فایل `FirstGame.apk` در مخزن)
- **نکته:** استفاده و یادگیری از کد آزاد است؛ گرافیک همراه بازی متعلق به شخص دیگری است و استفادهٔ تجاری از آن مجاز نیست — همان‌طور که در خود مخزن تصریح شده

## حوزه‌های کاری و ابزارها

- **رباتیک و شبیه‌سازی** — MATLAB، ابزار پیتر کروک، الگوریتم ژنتیک، مصورسازی سه‌بعدی
- **مهندسی دات‌نت** — C#، WPF/MVVM، Entity Framework Core، SQLite، تزریق وابستگی، AutoMapper
- **بازی‌سازی** — HTML5 Canvas، جاوااسکریپت، Lua / LÖVE 2D، خط تولید اسپرایت و صدای رویه‌ای
- **وب و موبایل** — Angular، TypeScript، Flutter/Dart
- **سیستم‌های سطح پایین** — پردازش تصویر، تحلیل بسته‌های شبکه با Scapy

<div align="center">
  <img src="https://img.shields.io/badge/MATLAB-00FF41?style=flat-square&logo=mathworks&logoColor=00FF41&labelColor=020604" alt="MATLAB" />
  <img src="https://img.shields.io/badge/C%23-00FF41?style=flat-square&logo=csharp&logoColor=00FF41&labelColor=020604" alt="C#" />
  <img src="https://img.shields.io/badge/.NET-00FF41?style=flat-square&logo=.net&logoColor=00FF41&labelColor=020604" alt=".NET" />
  <img src="https://img.shields.io/badge/JavaScript-00FF41?style=flat-square&logo=javascript&logoColor=00FF41&labelColor=020604" alt="JavaScript" />
  <img src="https://img.shields.io/badge/Lua-00FF41?style=flat-square&logo=lua&logoColor=00FF41&labelColor=020604" alt="Lua" />
  <img src="https://img.shields.io/badge/Angular-00FF41?style=flat-square&logo=angular&logoColor=00FF41&labelColor=020604" alt="Angular" />
  <img src="https://img.shields.io/badge/Flutter-00FF41?style=flat-square&logo=flutter&logoColor=00FF41&labelColor=020604" alt="Flutter" />
</div>

## گیت‌هاب در یک نگاه

<div align="center">
  <img src="assets/github-stats.svg?v=3" width="480" alt="کارت آمار با ظاهر ترمینال ماتریکس: مخزن‌های عمومی، ستارهٔ مخزن‌های شمرده‌شده، کامیت‌ها از ایندکس جست‌وجوی عمومی، دنبال‌کننده‌ها و استریک جاری" />
  <br/>
  <img src="assets/top-langs.svg?v=3" width="480" alt="کارت زبان‌ها با ظاهر ترمینال ماتریکس: سهم بایت کد در مخزن‌های عمومی شمرده‌شده" />
</div>

این کارت‌ها هر روز توسط GitHub Actions از دادهٔ عمومی بازتولید می‌شوند. شمارندهٔ کامیت از ایندکس جست‌وجوی کامیت عمومی گیت‌هاب می‌آید و سهم زبان‌ها بر پایهٔ بایت کد در مخزن‌های عمومی غیرفورک است — یک سنجهٔ حجم، نه سنجهٔ مهارت.

---

<div align="center">
  <code>> EOF · code, robots & games — built in the open on GitHub</code>
</div>

</div>
