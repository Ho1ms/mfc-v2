
import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Lang = "ru" | "en";
type Dict = Record<string, string>;

export function isLang(value: string): value is Lang {
  return value === 'ru' || value === 'en';
}

const DICT: Record<Lang, Dict> = {
  ru: {
    "home:main:home": "Главная",
    "home:main:greet": "Привет",
    "home:main:greeting": "Здравствуйте",
    "home:main:subtitle": "Что вас интересует?",
    "home:main:my_submissions": "Мои заявки",
    "home:main:my_submissions_sub": "История и статусы",
    "home:main:services": "Список услуг",
    "home:main:services_sub": "Подать заявку",
    "home:main:faq": "FAQ",
    "home:main:faq_sub": "Частые вопросы",
    "home:main:profile": "Профиль",
    "home:main:profile_sub": "Личные данные",

    "services:main:services": "Список услуг",
    "services:main:services_sub": "Справки и сервисы МФЦ",
    "services:main:profile_incomplete": "Заполните профиль (ФИО, дата рождения, группа) — без этого подача заявок недоступна.",
    "services:main:available_forms": "Доступные справки",
    "services:main:no_forms": "Формы пока не настроены.",
    "services:main:ban_forms": "Подача заявок заблокирована.",
    "services:main:status_error": "Не удалось получить статус",
    "services:main:check_stats": "Проверить номер заявки в ОСЭД",
    "services:main:request_number": "Номер заявки",
    "services:main:request_number_placeholder": "Например: 1122",
    "services:main:search": "Поиск",
    "services:main:searching": "Ищем…",
    "services:main:current_status": "Текущий статус",
    "services:main:unsubscribe": "Отписаться от уведомлений",
    "services:main:subscribe": "Подписаться на изменения",
    "services:main:subscribed_msg": "Мы пришлём уведомление в MAX, как только статус изменится.",
    "services:main:subscribe_msg": "Подписавшись, вы будете получать уведомления о смене статуса.",
    "services:main:no_find": "Не найдено",
    "services:main:checked_at": "Обновлено",
    "services:main:active_subscription": "Активная подписка",

    "services:form:last_name": "Фамилия",
    "services:form:first_name": "Имя",
    "services:form:patronymic": "Отчество",
    "services:form:birth_date": "Дата рождения",
    "services:form:study_group": "Номер группы",
    "services:form:profile_incomplete": "Заполните профиль (ФИО, дата рождения, группа) — без этого подача заявок недоступна.",
    "services:form:to_profile": "К профилю",
    "services:form:title": "Подача заявки",
    "services:form:email": "Почта",
  
    "submit:button:default": "Отправить заявку",
    "submit:button:loading": "Отправляем…",

    "word:reason": "Причина",
    "word:profile": "Профиль",
    "word:submission": "Заявка",
    "word:create_at": "Создана",
    "word:form_data": "Данные формы",
    "word:field": "Поле",
    "word:developing": "В разработке",
    
    "submit:error:profile_empty": "Сначала заполните профиль",
    "submit:error:loading_form": "Не удалось открыть форму",
    "submit:error:form_ban": "Вам был запрещён доступ к подаче форм.",
    "submit:error:generic": "Не удалось отправить заявку",
    "submit:error:ban_app": "Вам был запрещён доступ к приложению.",
    "submit:error:field_required": "Поле «{{field}}» обязательно",
    "submit:error:field_format": "Поле «{{field}}» не соответствует формату",
    "submit:error:field_number": "Поле «{{field}}» должно быть числом",
    "submit:error:field_min": "«{{field}}»: минимум {{min}}",
    "submit:error:field_max": "«{{field}}»: максимум {{max}}",
    "submit:error:field_date_min": "«{{field}}»: не раньше {{min}}",
    "submit:error:field_date_max": "«{{field}}»: не позже {{max}}",

    "history:main:title": "Мои заявки",
    "history:main:subtitle": "История подачи и статусы обработки",
    "history:main:no_submissions": "Заявок пока нет.",
    "history:main:status_history": "История статусов",

    "profile:main:title": "Профиль",
    "profile:main:subtitle": "Эти данные подставятся в формы автоматически",
    "profile:main:save": "Сохранить",
    "profile:main:saving": "Сохраняем…",
    "profile:main:incomplete": "Заполните профиль (ФИО, дата рождения, группа) — без этих данных подача заявок недоступна.",
    "profile:main:phone": "Телефон",
    "profile:main:phone_unverified": "не подтверждён",
    "profile:main:verify_phone": "Подтвердить телефон",
    "profile:main:phone_verification_not_available": "Подтверждение телефона доступно только в мини-приложении MAX.",
    "profile:main:personnel_number": "Табельный номер РУТ (МИИТ)",
    "profile:main:link_rut": "Привязать табельный номер РУТ (МИИТ)",
    "logo-miit-white": "logo-miit-white.png",
  },
  en: {
    "home:main:home": "Home",
    "home:main:greet": "Hi",
    "home:main:greeting": "Hello",
    "home:main:subtitle": "What are you interested in?",
    "home:main:my_submissions": "My history",
    "home:main:my_submissions_sub": "History and statuses",
    "home:main:services": "Services",
    "home:main:services_sub": "Submit a request",
    "home:main:faq": "FAQ",
    "home:main:faq_sub": "Frequently Asked Questions",
    "home:main:profile": "Profile",
    "home:main:profile_sub": "Personal data",

    "services:main:services": "Services",
    "services:main:services_sub": "References and services of MFC",
    "services:main:profile_incomplete": "Complete your profile (full name, birth date, group) — without this, submitting requests is unavailable.",
    "services:main:available_forms": "Available forms",
    "services:main:no_forms": "No forms configured yet.",
    "services:main:ban_forms": "Form submission is blocked.",
    "services:main:status_error": "Failed to get status",
    "services:main:check_stats": "Check request number in OSED",
    "services:main:request_number": "Request number",
    "services:main:request_number_placeholder": "For example: 1122",
    "services:main:search": "Search",
    "services:main:searching": "Searching…",
    "services:main:current_status": "Current status",
    "services:main:unsubscribe": "Unsubscribe from notifications",
    "services:main:subscribe": "Subscribe to changes",
    "services:main:subscribed_msg": "We'll send a notification to MAX as soon as the status changes.",
    "services:main:subscribe_msg": "By subscribing, you will receive notifications about status changes.",
    "services:main:no_find": "Not found",
    "services:main:checked_at": "Checked at",
    "services:main:active_subscription": "Active subscription",

    "services:form:first_name": "First name",
    "services:form:last_name": "Last name",
    "services:form:patronymic": "Patronymic",
    "services:form:birth_date": "Birth date",
    "services:form:study_group": "Study group",

    "services:form:profile_incomplete": "Complete your profile (full name, birth date, group) — without this, submitting requests is unavailable.",
    "services:form:to_profile": "To profile",
    "services:form:title": "Submit a request",


    "word:reason": "Reason",
    "word:profile": "Profile",
    "word:submission": "Submission",
    "word:create_at": "Created at",
    "word:form_data": "Form data",
    "word:field": "Field",
    "history:main:status_history": "Status history",


    "submit:button:default": "Submit request",
    "submit:button:loading": "Submitting…",
    "submit:error:profile_empty": "Please complete your profile first",
    "submit:error:loading_form": "Failed to load form",
    "submit:error:form_ban": "You have been banned from submitting forms.",
    "submit:error:generic": "Failed to submit form",
    "submit:error:ban_app": "You have been banned from using the app.",
    "submit:error:field_required": "Field «{{field}}» is required",
    "submit:error:field_format": "Field «{{field}}» does not match the format",
    "submit:error:field_number": "Field «{{field}}» must be a number",
    "submit:error:field_min": "«{{field}}»: minimum {{min}}",
    "submit:error:field_max": "«{{field}}»: maximum {{max}}",
    "submit:error:field_date_min": "«{{field}}»: not earlier than {{min}}",
    "submit:error:field_date_max": "«{{field}}»: not later than {{max}}",

    "history:main:title": "My submissions",
    "history:main:subtitle": "Submission history and processing statuses",
    "history:main:no_submissions": "No submissions yet.",

    "profile:main:title": "Profile",
    "profile:main:subtitle": "This data will be automatically filled in the forms",
    "profile:main:save": "Save",
    "profile:main:saving": "Saving…",
    "profile:main:incomplete": "Complete your profile (full name, birth date, group) — without this data, submitting requests is unavailable.",
    "profile:main:phone": "Phone",
    "profile:main:phone_unverified": "unverified",
    "profile:main:verify_phone": "Verify phone",
    "profile:main:phone_verification_not_available": "Phone verification is only available in the MAX mini-app.",
    "profile:main:personnel_number": "Personnel number RUT (MIIT)",
    "profile:main:link_rut": "Link RUT (MIIT) personnel number",
    "logo-miit-white": "logo-miit-white-en.png",
  },
};

const LS_KEY = "mfc.client.lang";

function detectInitial(): Lang {
  const saved = (sessionStorage.getItem(LS_KEY) || "").toLowerCase();
  if (saved === "ru" || saved === "en") return saved;
  const nav = (navigator.language || "").toLowerCase();
  console.log("Detecting language from navigator:", nav);
  return nav.startsWith("ru") ? "ru" : "en";
}

interface I18nState {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;

}

const Ctx = createContext<I18nState | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {

  const [lang, setLangState] = useState<Lang>(detectInitial);

  useEffect(() => {
    console.log("Setting language to", lang);
    sessionStorage.setItem(LS_KEY, lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => setLangState(l), []);
  const t = useCallback((key: string, vars?: Record<string, string | number>) => {
    let str = DICT[lang][key] ?? DICT.ru[key] ?? key;
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        str = str.replace(new RegExp(`{{${k}}}`, 'g'), String(v));
      });
    }
    return str;
}, [lang]);
  const value = useMemo<I18nState>(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return createElement(Ctx.Provider, { value }, children);
}

export function useI18n(): I18nState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useI18n must be used within I18nProvider");
  return v;
}
