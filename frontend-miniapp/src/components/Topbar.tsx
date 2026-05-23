
import {useI18n} from "@/i18n";

export function Topbar() {
  const { t } = useI18n();
  console.log(t("logo-miit-white"));
  return (
    <header className="topbar">
        <img src={t("logo-miit-white")} alt="" style={{  maxHeight: "30px", objectFit: "contain" }} />
    </header>
  );
}
