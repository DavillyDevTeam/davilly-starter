from apps.api.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, negotiate, t


def test_default_locale_is_supported() -> None:
    assert DEFAULT_LOCALE in SUPPORTED_LOCALES


def test_landing_title_is_translated() -> None:
    title = t("common.landing.title", DEFAULT_LOCALE)
    assert title != "common.landing.title"
    assert len(title) > 0


def test_negotiate_unknown_uses_default() -> None:
    assert negotiate("zz") == DEFAULT_LOCALE
    assert negotiate(None) == DEFAULT_LOCALE


def test_negotiate_matches_a_supported_tag() -> None:
    chosen = SUPPORTED_LOCALES[0]
    assert negotiate(chosen) == chosen


def test_negotiate_maps_primary_or_region() -> None:
    locale = SUPPORTED_LOCALES[0]
    if "-" in locale:
        assert negotiate(locale.split("-", 1)[0]) == locale
    else:
        assert negotiate(f"{locale}-GB") == locale


def test_negotiate_prefers_higher_quality() -> None:
    if len(SUPPORTED_LOCALES) < 2:
        return
    preferred = SUPPORTED_LOCALES[0]
    other = SUPPORTED_LOCALES[1]
    assert negotiate(f"{other};q=0.1, {preferred};q=0.9") == preferred
