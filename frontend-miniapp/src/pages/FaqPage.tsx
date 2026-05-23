import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Faq } from "@/api/types";
import { Icon } from "@/components/Icon";
import { useAuth } from "@/auth/AuthProvider";

export function FaqPage() {
  const { profile } = useAuth();
  const isEn = profile?.language_code && !profile.language_code.toLowerCase().startsWith("ru");
  const [items, setItems] = useState<Faq[]>([]);
  const [openId, setOpenId] = useState<number | null>(null);

  useEffect(() => {
    void api.get<Faq[]>("/faq").then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div className="screen">
      <h1 className="screen-title">{isEn ? "FAQ" : "Частые вопросы"}</h1>
      <p className="screen-sub">{isEn ? "Tap a question to expand" : "Нажмите на вопрос, чтобы развернуть ответ"}</p>

      {items.length === 0 && (
        <div className="card" style={{ textAlign: "center", color: "var(--ink-400)" }}>
          {isEn ? "No FAQ yet" : "Пока вопросов нет"}
        </div>
      )}

      {items.map((it) => {
        const question = isEn && it.question_en ? it.question_en : it.question;
        const answer = isEn && it.answer_en ? it.answer_en : it.answer;
        const open = openId === it.id;
        return (
          <div key={it.id} className="faq-item">
            <div className="faq-q" onClick={() => setOpenId(open ? null : it.id)}>
              <span>{question}</span>
              <span className="ico" style={{ width: 18, height: 18, color: "var(--ink-400)", transform: open ? "rotate(180deg)" : "none", transition: "transform .15s" }}>
                <Icon.ChevronDown />
              </span>
            </div>
            {open && <div className="faq-a">{answer}</div>}
          </div>
        );
      })}
    </div>
  );
}
