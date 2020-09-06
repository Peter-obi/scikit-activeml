import numpy as np
import unittest

from sklearn.datasets import load_breast_cancer
from sklearn.utils.validation import NotFittedError, check_is_fitted
from sklearn.gaussian_process import GaussianProcessClassifier, \
    GaussianProcessRegressor
from sklearn.naive_bayes import GaussianNB
from skactiveml.classifier import SklearnClassifier


class TestClassifierWrapper(unittest.TestCase):

    def setUp(self):
        self.X = np.zeros((4, 1))
        self.y1 = ['tokyo', 'paris', 'nan', 'tokyo']
        self.y2 = ['tokyo', 'nan', 'nan', 'nan']

    def test_init(self):
        self.assertRaises(TypeError, SklearnClassifier, estimator=None)
        self.assertRaises(TypeError, SklearnClassifier,
                          estimator=GaussianProcessRegressor())
        self.assertRaises(TypeError, SklearnClassifier,
                          estimator=GaussianProcessClassifier(),
                          missing_label=[2])
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                random_state=0)
        self.assertFalse(hasattr(clf, 'classes_'))
        self.assertRaises(NotFittedError, check_is_fitted, estimator=clf)
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                missing_label='nan',
                                classes=['tokyo', 'paris'], random_state=0)
        np.testing.assert_array_equal(['paris', 'tokyo'], clf.classes_)
        np.testing.assert_array_equal(['paris', 'tokyo'], clf._le._le.classes_)
        self.assertEqual(clf.kernel, clf.estimator.kernel)
        self.assertFalse(hasattr(clf, 'kernel_'))

    def test_fit(self):
        clf = SklearnClassifier(estimator=GaussianProcessClassifier())
        self.assertRaises(NotFittedError, check_is_fitted, estimator=clf)
        self.assertRaises(ValueError, clf.fit, X=[], y=[])
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                classes=['tokyo', 'paris', 'new york'],
                                missing_label='nan')
        check_is_fitted(estimator=clf)
        self.assertFalse(clf.is_fitted_)
        clf.fit(self.X, self.y1)
        self.assertTrue(clf.is_fitted_)
        self.assertTrue(hasattr(clf, 'kernel_'))
        np.testing.assert_array_equal(clf.classes_, ['new york', 'paris',
                                                     'tokyo'])
        self.assertEqual(clf.missing_label, 'nan')
        clf.fit(self.X, self.y2)
        self.assertFalse(clf.is_fitted_)
        self.assertFalse(hasattr(clf, "kernel_"))
        self.assertFalse(hasattr(clf, 'partial_fit'))

    def test_partial_fit(self):
        clf = SklearnClassifier(estimator=GaussianNB())
        self.assertRaises(ValueError, clf.partial_fit, X=[], y=[])
        clf = SklearnClassifier(estimator=GaussianNB(),
                                classes=['tokyo', 'paris', 'new york'],
                                missing_label='nan')
        check_is_fitted(estimator=clf)
        self.assertFalse(clf.is_fitted_)
        clf.partial_fit(self.X, self.y1)
        self.assertTrue(clf.is_fitted_)
        self.assertTrue(hasattr(clf, 'class_count_'))
        np.testing.assert_array_equal(clf.classes_, ['new york', 'paris',
                                                     'tokyo'])
        self.assertEqual(clf.missing_label, 'nan')
        clf.partial_fit(self.X, self.y2)
        self.assertTrue(clf.is_fitted_)
        self.assertFalse(hasattr(clf, "kernel_"))
        self.assertTrue(hasattr(clf, 'partial_fit'))

    def test_predict_proba(self):
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                missing_label='nan')
        self.assertRaises(NotFittedError, clf.predict_proba, X=self.X)
        clf.fit(X=self.X, y=self.y1)
        P = clf.predict_proba(X=self.X)
        est = GaussianProcessClassifier().fit(X=np.zeros((3, 1)),
                                              y=['tokyo', 'paris', 'tokyo'])
        P_exp = est.predict_proba(X=self.X)
        np.testing.assert_array_equal(P_exp, P)
        np.testing.assert_array_equal(clf.classes_, est.classes_)
        clf.fit(X=self.X, y=self.y2)
        P = clf.predict_proba(X=self.X)
        P_exp = np.ones((len(self.X), 1))
        np.testing.assert_array_equal(P_exp, P)
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                classes=['ny', 'paris', 'tokyo'],
                                missing_label='nan')
        P = clf.predict_proba(X=self.X)
        P_exp = np.ones((len(self.X), 3)) / 3
        np.testing.assert_array_equal(P_exp, P)
        clf.fit(X=self.X, y=self.y1)
        P = clf.predict_proba(X=self.X)
        P_exp = np.zeros((len(self.X), 3))
        P_exp[:, 1:] = est.predict_proba(X=self.X)
        np.testing.assert_array_equal(P_exp, P)

    def test_predict(self):
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                missing_label='nan')
        self.assertRaises(NotFittedError, clf.predict, X=self.X)
        clf.fit(X=self.X, y=self.y1)
        y = clf.predict(X=self.X)
        est = GaussianProcessClassifier().fit(X=np.zeros((3, 1)),
                                              y=['tokyo', 'paris', 'tokyo'])
        y_exp = est.predict(X=self.X)
        np.testing.assert_array_equal(y, y_exp)
        np.testing.assert_array_equal(clf.classes_, est.classes_)
        clf.fit(X=self.X, y=self.y2)
        y = clf.predict(X=self.X)
        y_exp = ['tokyo'] * len(self.X)
        np.testing.assert_array_equal(y_exp, y)
        clf = SklearnClassifier(estimator=GaussianProcessClassifier(),
                                classes=['ny', 'paris', 'tokyo'],
                                missing_label='nan', random_state=0)
        y = clf.predict(X=[[0]] * 1000)
        self.assertTrue(len(np.unique(y)) == len(clf.classes_))
        clf.fit(X=self.X, y=self.y1)

    def test_multi_annotator_scenario(self):
        X, y_true = load_breast_cancer(return_X_y=True)
        y = np.repeat(y_true.reshape(-1, 1), 2, axis=1)
        y[:100, 0] = -1
        y[200:, 0] = -1
        sample_weights = np.ones_like(y) * 0.9
        clf = SklearnClassifier(estimator=GaussianNB(),
                                missing_label=-1, random_state=0)
        clf.fit(X[:250], y[:250], sample_weight=sample_weights[:250])
        self.assertTrue(clf.score(X[250:], y_true[250:]) > 0.5)


if __name__ == '__main__':
    unittest.main()
