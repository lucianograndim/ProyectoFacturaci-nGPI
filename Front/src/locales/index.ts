import { Locales } from "./i18n";

import en from "./en.json";
import es from "./es.json";

export const messages = {
  [Locales.EN]: en,
  [Locales.ES]: es
};

export const defaultLocale = Locales.ES;