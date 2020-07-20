import pandas as pd
from sklearn.linear_model import Ridge

from Pythagoras.util import *
from Pythagoras.logging import *
from Pythagoras.feature_engineering import *
from Pythagoras.caching import *


# Workaround to ensure compatibility with Python <= 3.6
# Versions 3.6 and below do not support postponed evaluation



class CV_Score(LoggableObject):
    def __init__(self, model, n_splits=3, n_repeats=9, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rkf = RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats)
        self.model = clone(model)

    def __call__(self, X, y, ):
        self.scores_ = cross_val_score(
            self.model, X, y, cv=self.rkf, scoring="r2"
            ,error_score="raise", n_jobs = -1)
        mean_score = np.mean(self.scores_)
        median_score = np.median(self.scores_)
        return min(mean_score, median_score)


class PRegressor(PEstimator):
    target_name_: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_fitting(self
                      , X: Any
                      , y: Any
                      , write_to_log: bool = True
                      ) -> Tuple[pd.DataFrame, pd.Series]:
        X, y = super().start_fitting(X, y)
        self.target_name_ = y.name
        self.min_med_max_ = (min(y), percentile50(y), max(y))
        return X, y

    def start_predicting(self
                         , X: pd.DataFrame
                         , write_to_log: bool = True
                         ) -> pd.DataFrame:

        assert self.is_fitted_
        assert len(X)

        if write_to_log:
            log_message = f"==> Starting generating predictions "
            log_message += f"using a {type(X).__name__} named < "
            log_message += NeatStr.object_names(X, div_ch=" / ")
            log_message += f" > with the shape {X.shape}."
            self.info(log_message)

        X = self._fix_X(X)
        assert set(self.input_columns_) <= set(X)
        X = deepcopy(X[self.input_columns_])

        if not self.input_can_have_nans:
            assert X.isna().sum().sum() == 0

        return X

    def finish_predicting(self
                          , y: pd.Series
                          , write_to_log: bool = True
                          ) -> pd.Series:

        assert len(y)

        n_val = len(y)
        p_min_med_max = (min(y), percentile50(y), max(y))
        n_nans = y.isna().sum()

        if write_to_log:
            log_message = f"<== Predictions for {y.name} have been created. "
            log_message += f"The result contains {n_val} values "
            log_message += f"with {n_nans} NaN-s, with the following "
            log_message += f"min, median, max: {p_min_med_max}; "
            log_message += f"while the taining data had {self.min_med_max_}."
            self.info(log_message)

        if not self.output_can_have_nans:
            assert n_nans == 0

        y.name = self.target_name_

        return y



class SimpleGarden(PRegressor):
    pass


class SimpleGarden(PRegressor):

    def __init__(self
                 , *args
                 , **kwargs
                 ) -> None:

        super().__init__(*args, **kwargs)
        self.set_params(**kwargs)

    def set_params(self
                   , base_model_type=Ridge
                   , base_model_params={"alpha": 0.01, "normalize": True}
                   , feature_cr_threshold: float = 0.075
                   , max_features_per_omodel: Optional[int] = None
                   , max_omodels_per_garden: int = 10
                   , cv_score_threshold: Optional[float] = None
                   , cv_score_threshold_multiplier: Optional[float] = 0.75
                   , n_folds: int = 5
                   ) -> SimpleGarden:

        assert (int(cv_score_threshold is None) +
                int(cv_score_threshold_multiplier is None) == 1)

        if cv_score_threshold is not None:
            assert 0 < cv_score_threshold < 1

        if cv_score_threshold_multiplier is not None:
            assert 0 < cv_score_threshold_multiplier < 1

        self.base_model_ = base_model_type(**base_model_params)
        self.base_model_cv_score = CV_Score(self.base_model_)
        self.feature_cr_threshold = feature_cr_threshold
        self.max_features_per_omodel = max_features_per_omodel
        self.n_folds = n_folds
        self.max_omodels_per_garden = max_omodels_per_garden
        self.cv_score_threshold = cv_score_threshold
        self.cv_score_threshold_multiplier = cv_score_threshold_multiplier

        self.omodels_ = []
        self.feature_lists_ = []
        self.cv_scores_ = []
        self.log_df_ = None
        self.fit_cv_score_threshold_ = None

        return self

    def get_params(self, deep: bool = False) -> Dict[str, Any]:

        result = {"base_model_type": type(self.base_model_)
            , "base_model_params": self.base_model_.get_params()
            , "feature_cr_threshold": self.feature_cr_threshold
            , "max_features_per_omodel": self.max_features_per_omodel
            , "max_omodels_per_garden": self.max_omodels_per_garden
            , "cv_score_threshold": self.cv_score_threshold
            ,
                  "cv_score_threshold_multiplier": self.cv_score_threshold_multiplier
            , "n_folds": self.n_folds}

        return result

    @property
    def input_columns_(self) -> List[str]:
        return sorted([c for l in self.feature_lists_ for c in l])

    @property
    def input_can_have_nans(self) -> bool:
        return False

    @property
    def output_can_have_nans(self) -> bool:
        return False

    def one_best_feature(self
                         , X: pd.DataFrame
                         , y: pd.Series
                         ) -> Tuple[str, float]:
        cr = pd.DataFrame(np.abs(X.corrwith(y)))
        cr.sort_values(by=cr.columns[0], ascending=False, inplace=True)
        best_feature = cr.index[0]
        corr_best_feature = cr.iloc[0, 0]
        return (best_feature, corr_best_feature)

    @property
    def is_fitted_(self) -> bool:
        return bool(len(self.omodels_))

    def fit(self
            , X: pd.DataFrame
            , y: pd.Series
            ) -> SimpleGarden:

        X, y = self.start_fitting(X, y)

        self.omodels_ = []
        self.feature_lists_ = []
        self.cv_scores_ = []
        self.log_df_ = None
        omodel_logs = []
        self.fit_cv_score_threshold_ = self.cv_score_threshold
        unprocessed_features = set(X.columns)

        if self.max_features_per_omodel is not None:
            self.current_max_max_features_per_omodel = (
                self.max_features_per_omodel)
        else:
            self.current_max_max_features_per_omodel = int(len(X) ** 0.5)
            log_message = "max_features_per_omodel was not provided, "
            log_message += f"defaulting to square root of number of samples "
            log_message += f"({self.current_max_max_features_per_omodel})"
            self.info(log_message)

        recommended_min_features = (self.current_max_max_features_per_omodel
                                    * self.max_omodels_per_garden * 3)

        if recommended_min_features > len(X.columns):
            log_message = f"NUMBER OF FEATURES {len(X.columns)} IS TOO LOW, "
            log_message += f"RECOMMENDED MIN # IS {recommended_min_features}"
            self.warning(log_message)

        for i in range(self.max_omodels_per_garden):
            log_message = f"Attempting to build {i + 1}-th "
            log_message += f"(out of {self.max_omodels_per_garden}) "
            log_message += f"model in a garden. "
            self.info(log_message)

            X_new = X[sorted(list(unprocessed_features))]

            (model_i, features_i, cv_score_i, log_i) = (
                self.build_an_omodel(X_new, y))

            if self.fit_cv_score_threshold_ is None:
                self.fit_cv_score_threshold_ = (
                        cv_score_i * self.cv_score_threshold_multiplier)

            if cv_score_i < self.fit_cv_score_threshold_:
                log_message = f"OModel # {i + 1} did not reach a minumum cv_score"
                log_message += f" threshold of {self.fit_cv_score_threshold_:.2%}"
                log_message += f" and it will not be included into the garden"
                log_message += f", now stopping model-building process. "
                self.info(log_message)
                break

            self.omodels_ += [model_i]
            self.feature_lists_ += [sorted(features_i)]
            self.cv_scores_ += [cv_score_i]
            log_i["ModelID"] = i
            omodel_logs += [log_i]
            unprocessed_features -= set(features_i)

        n_models = len(self.omodels_)
        n_features_used = len(X.columns) - len(unprocessed_features)
        if n_models == 0:
            self.error("No omodels were created for the garden")
        else:
            self.log_df_ = pd.concat(omodel_logs, ignore_index=True)
            assert n_models == self.log_df_["ModelID"].nunique()
            assert n_features_used == (
                self.log_df_[self.log_df_.In_Model]["Feature"].nunique())

        log_message = f"<== {n_models} models were created"
        log_message += f" and included into the garden, alltogether using "
        log_message += f"{n_features_used} features out of {len(X.columns)} "
        log_message += f"available, cv_scores are {self.cv_scores_}."
        self.info(log_message)

        return self

    def predict(self, X
                ) -> pd.Series:

        X = self.start_predicting(X)
        self.last_opredictions_ = []
        n_models = len(self.omodels_)

        for i in range(n_models):
            self.last_opredictions_ += [
                self.omodels_[i].predict(X[sorted(self.feature_lists_[i])])]

        ## TODO: refactor mean calculations below
        result = self.last_opredictions_[0]
        for i in range(1, n_models):
            result += self.last_opredictions_[i]
        if n_models > 1:
            result /= n_models

        result = pd.Series(
            data=result, index=X.index, name=self.target_name_)

        return self.finish_predicting(result)

    def build_an_omodel(self
                        , X: pd.DataFrame
                        , y: pd.Series
                        ):
        X = deepcopy(X)
        y = deepcopy(y)
        work_model = clone(self.base_model_)
        status_log = pd.DataFrame(
            columns=["Feature", "Correlation", "CV_Score"])

        num_iter = 1
        (first_feature, corr) = self.one_best_feature(X, y)
        remaining_features = list(X.columns)
        remaining_features.remove(first_feature)
        selected_features = [first_feature]
        cv_score = self.base_model_cv_score(X[sorted(selected_features)], y)
        work_model.fit(X[sorted(selected_features)], y)
        predictions = work_model.predict(X[sorted(selected_features)])
        residuals = predictions - y
        status_log = status_log.append(
            {"Feature": first_feature, "Correlation": corr
                , "CV_Score": cv_score}
            , ignore_index=True)

        while (len(remaining_features)
               and corr >= self.feature_cr_threshold
               and num_iter < self.current_max_max_features_per_omodel):
            num_iter += 1
            (new_feature, corr) = self.one_best_feature(
                X[remaining_features], residuals)
            remaining_features.remove(new_feature)
            selected_features.append(new_feature)
            cv_score = self.base_model_cv_score(X[sorted(selected_features)],
                                                y)
            work_model = work_model.fit(X[sorted(selected_features)], y)
            predictions = work_model.predict(X[sorted(selected_features)])
            residuals = predictions - y
            status_log = status_log.append(
                {"Feature": new_feature, "Correlation": corr
                    , "CV_Score": cv_score}
                , ignore_index=True)

        best_iteration = status_log["CV_Score"].idxmax()
        best_features = sorted(selected_features[:best_iteration + 1])
        best_model = work_model.fit(X[sorted(best_features)], y)
        best_cv_score = status_log.at[best_iteration, "CV_Score"]
        status_log["In_Model"] = (status_log.index <= best_iteration)
        status_log["Rank"] = status_log.index

        log_message = f"<== New OModel has been built. The model has reached "
        log_message += f"the best cv_sore of {best_cv_score:.2%} on its "
        log_message += f"{best_iteration + 1} feature-search iteration "
        log_message += f"(out of {self.current_max_max_features_per_omodel})."
        self.info(log_message)

        assert (set(best_features) ==
                set(status_log[status_log.In_Model]["Feature"].unique()))

        return best_model, best_features, best_cv_score, status_log