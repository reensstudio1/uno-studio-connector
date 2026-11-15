# Uno Studio — חיבור ל-Claude Code

החיבור נותן ל-Claude Code כלים לעבודה עם **Uno Studio שמותקן אצלך**:
- רשימת פרויקטים וקריאת קאט;
- הוספת שכבות, זום וצבע;
- ייצוא.

כל שינוי נשמר **כגרסה חדשה** ב-projects/. הקאט המקורי והמדיה לא משתנים.

החיבור לא כולל את האפליקציה, פרויקטים או מדיה. הוא מוצא את תיקיית Uno במחשב ומפעיל את השרת שמגיע עם Uno עצמו.

## לפני שמתחילים
- Uno Studio מותקן (התיקייה עם «Uno Studio.app»), ונפתח פעם אחת.
- Claude Code מותקן.
- Mac. ‏Windows עדיין לא נתמך.

## התקנה — בקשה אחת להעתקה ל-Claude Code
> התקן את החיבור של Uno Studio מ-https://github.com/reensstudio1/uno-studio-connector: הורד את `install.sh` מה-repo, הצג לי מה הוא עושה, הרץ אותו עם bash, ובסוף הראה לי את התוצאה של `claude mcp list`.

## או ידנית בטרמינל
```bash
curl -fsSLO https://raw.githubusercontent.com/reensstudio1/uno-studio-connector/main/install.sh
bash install.sh
```

**מה הסקריפט עושה:**
- בודק ש-claude, ‏python3 ו-git קיימים;
- מגבה את הגדרות Claude Code ל-`~/.claude/backups/uno-connector-<זמן>/`;
- מוסיף את החיבור. חיבורי MCP ותוספים אחרים לא נמחקים.

## איפה רואים שזה מחובר
- **ב-Claude Code:** אחרי הפעלה מחדש, `/mcp` מציג את `plugin:uno-studio:uno-studio` עם ✓, ו-`/plugin` מציג את `uno-studio` תחת Installed.
- **בטרמינל:** `claude mcp list`.

## בדיקה ראשונה
> Use uno-studio: list my projects, read "תרגיל 1 - קאט ראשון", and make a copy with a title "בדיקה" from 1 to 3 seconds.

## עדכון, גרסה מסוימת וחזרה
```bash
bash install.sh                    # הגרסה החדשה ביותר (רק כשאתה מריץ — אין עדכון אוטומטי)
bash install.sh --version v1.0.0   # גרסה מסוימת
bash install.sh --rollback         # חזרה לגרסה הקודמת
```

## אם Uno לא נמצא
הכלי `uno_status` מסביר מה חסר. אפשר לקבוע את התיקייה ידנית:
```bash
python3 ~/.uno-studio-connector/releases/<גרסה>/plugins/uno-studio/connector/uno_connector.py --set-root "/path/to/Uno Studio"
```

**הסרה:** `claude plugin uninstall uno-studio@uno-studio` ואז `claude plugin marketplace remove uno-studio`.
