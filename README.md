# Uno Studio — MCP מקומי ל-Claude Desktop

חיבור מקומי לעריכת Uno, שמופיע ב־**Customize → Connectors → Yours** בשם `uno-studio`, בדומה לחיבורים מקומיים של תוכנות עריכה. ברירת המחדל אינה מתקינה Plugin.

## לפני ההתקנה
- Mac עם Claude Desktop ו-Uno Studio מותקנים. פתחו את Uno פעם אחת.
- Python 3 ו-Git זמינים. אין צורך ב-Claude Code CLI בשביל המתקין עצמו.
- Windows, דפדפן וטלפון אינם נתמכים במסלול מקומי זה.

## בקשה אחת ל-Claude
> התקן את ה-MCP המקומי של Uno Studio מ-https://github.com/reensstudio1/uno-studio-connector. קרא את ההוראות, בדוק את install.sh והרץ אותו. שמור חיבורים קיימים ואל תסגור עבודה פעילה ב-Claude. לאחר טעינת החיבור מחדש, הראה לי את uno-studio ב-Connectors ובדוק שינוי רק על עותק של פרויקט.

או הורידו את הריפו ופתחו טרמינל בתיקייה:
```bash
bash install.sh
```

המתקין מוריד גרסה מתויגת מ-GitHub, מגבה את הגדרות Claude ומוסיף רשומת MCP ל־`~/Library/Application Support/Claude/claude_desktop_config.json`. הוא שומר חיבורים והגדרות אחרים. אין מחיקת פלאגינים, הפעלה מחדש אוטומטית או שינוי בפרויקטים ובמדיה.

**אחרי שהעבודה הפעילה הסתיימה:** סגרו ופתחו את Claude Desktop ובדקו `Customize → Connectors → Yours → uno-studio`. ייתכן ש-Claude יבקש אישור לכלים. רישום בקובץ ההגדרות אינו הוכחה שהחיבור נטען.

## בדיקת עריכה
בקשו לקרוא פרויקט וליצור ממנו גרסה חדשה עם כותרת או זום, ולוודא שהמקור לא השתנה. שרת Uno שמגיע עם האפליקציה קובע את הכלים. אין צורך בשירות ענן או בפרסום המדיה.

## עדכון וחזרה
```bash
bash install.sh --version v1.1.0
bash install.sh --rollback
```
החזרה זמינה אחרי מעבר בין שתי גרסאות Desktop. גרסאות v1.0.x השתמשו ב-Plugin; הן אינן יעד לחזרה זו. אין עדכון אוטומטי.

## Uno לא נמצא?
פתחו את Uno פעם אחת. אם הותקן בתיקייה לא שגרתית:
```bash
python3 ~/.uno-studio-connector/releases/v1.1.0/plugins/uno-studio/connector/uno_connector.py --set-root "/path/to/Uno Studio"
```

קבצי הפלאגין הישנים נשארו לתאימות; המתקין החדש אינו מפעיל אותם. חיבור מקומי דורש אישור גישה במחשב גם כשהוא אינו פלאגין.
