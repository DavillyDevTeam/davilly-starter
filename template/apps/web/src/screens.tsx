import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { apiUrl, type Providers } from './api';

function ProviderLinks({ providers }: { providers: Providers }) {
  const { t } = useTranslation('common');
  if (!providers.google && !providers.github) return null;
  return (
    <div className="providers">
      {providers.google ? (
        <a href={apiUrl('/auth/google/authorize')}>{t('auth.continueWithGoogle')}</a>
      ) : null}
      {providers.github ? (
        <a href={apiUrl('/auth/github/authorize')}>{t('auth.continueWithGitHub')}</a>
      ) : null}
    </div>
  );
}

export function Login({
  error,
  providers,
  busy,
  onSubmit,
  onNavigate,
}: {
  error: string | null;
  providers: Providers;
  busy: boolean;
  onSubmit: (email: string, password: string) => void;
  onNavigate: (path: string) => void;
}) {
  const { t } = useTranslation('common');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <main className="auth">
      <h1>{t('auth.signIn')}</h1>
      {error !== null ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(email, password);
        }}
      >
        <label>
          {t('auth.email')}
          <input
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
          />
        </label>
        <label>
          {t('auth.password')}
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>
        <button className="primary" type="submit" disabled={busy}>
          {t('auth.signIn')}
        </button>
      </form>
      <ProviderLinks providers={providers} />
      <button
        type="button"
        className="linkish"
        onClick={() => {
          onNavigate('/register');
        }}
      >
        {t('auth.needAccount')}
      </button>
    </main>
  );
}

export function Register({
  error,
  providers,
  busy,
  onSubmit,
  onNavigate,
}: {
  error: string | null;
  providers: Providers;
  busy: boolean;
  onSubmit: (email: string, password: string) => void;
  onNavigate: (path: string) => void;
}) {
  const { t } = useTranslation('common');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const message = localError ?? error;
  return (
    <main className="auth">
      <h1>{t('auth.register')}</h1>
      {message !== null ? (
        <p className="error" role="alert">
          {message}
        </p>
      ) : null}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (password.length < 8) {
            setLocalError(t('auth.passwordShort'));
            return;
          }
          setLocalError(null);
          onSubmit(email, password);
        }}
      >
        <label>
          {t('auth.email')}
          <input
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
          />
        </label>
        <label>
          {t('auth.password')}
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>
        <button className="primary" type="submit" disabled={busy}>
          {t('auth.register')}
        </button>
      </form>
      <ProviderLinks providers={providers} />
      <button
        type="button"
        className="linkish"
        onClick={() => {
          onNavigate('/login');
        }}
      >
        {t('auth.haveAccount')}
      </button>
    </main>
  );
}

export function Account({
  email,
  onSignOut,
}: {
  email: string | null;
  onSignOut: () => void;
}) {
  const { t } = useTranslation('common');
  return (
    <main className="auth">
      <h1>{t('auth.account')}</h1>
      {email !== null ? (
        <p>
          {t('auth.signedInAs')} {email}
        </p>
      ) : null}
      <button className="primary" type="button" onClick={onSignOut}>
        {t('auth.signOut')}
      </button>
    </main>
  );
}
