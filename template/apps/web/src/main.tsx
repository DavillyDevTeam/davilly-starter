import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { author, copy, defaultLocale, projectName } from './copy';
import './style.css';

function Landing() {
  const [locale, setLocale] = useState(defaultLocale);
  const text = copy[locale];
  useEffect(() => { document.documentElement.lang = locale; }, [locale]);
  if (!text) return null;
  return <><header><a href="#">{projectName}<span>✦</span></a><nav aria-label="Language">{Object.entries(copy).map(([key, value]) => <button key={key} aria-pressed={locale === key} onClick={() => { setLocale(key); }}>{value.label}</button>)}</nav></header>
    <main><section className="hero"><p className="eyebrow">{text.eyebrow}</p><h1>{text.title}</h1><p className="description">{text.description}</p><a className="cta" href="#possibilities">{text.cta} <span>↗</span></a><div className="orbit" aria-hidden="true"><div>✦</div></div></section>
    <section id="possibilities" className="features">{text.features.map((feature, index) => <article key={feature}><span>0{index + 1}</span><h2>{feature}</h2></article>)}</section></main><footer>{projectName} · {text.footer} {author}</footer></>;
}
const root = document.getElementById('root');
if (!root) throw new Error('Missing root element');
createRoot(root).render(<StrictMode><Landing /></StrictMode>);
