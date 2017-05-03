
import os


def test_nbdime_js_artifacts_present():
    from nbdime.webapp import __file__ as webapp_init
    static_folder = os.path.join(os.path.dirname(webapp_init), 'static')
    targets = [os.path.join(static_folder, 'nbdime.js')]
    missing = [t for t in targets if not os.path.exists(t)]
    if missing:
        raise ValueError(('missing files: %s' % missing))
