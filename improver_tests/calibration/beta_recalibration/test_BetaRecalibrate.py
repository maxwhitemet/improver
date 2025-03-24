# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of 'IMPROVER' and is released under the BSD 3-Clause license.
# See LICENSE in the root of the repository for full licensing details.
from datetime import datetime

import iris
import numpy as np
import pytest
from iris.exceptions import CoordinateNotFoundError
from scipy.stats import beta

from improver.calibration.beta_recalibration import BetaRecalibrate
from improver.synthetic_data.set_up_test_cubes import (
    set_up_percentile_cube,
    set_up_probability_cube,
)
from improver.utilities.cube_manipulation import MergeCubes


@pytest.fixture
def forecast_grid():
    thresholds = [283, 288]
    forecast_data = np.arange(9, dtype=np.float32).reshape(3, 3) / 8.0
    forecast_data_stack = np.stack([forecast_data, forecast_data])
    forecast_1 = set_up_probability_cube(
        forecast_data_stack,
        thresholds,
        time=datetime(2017, 11, 11, 4, 0),
        frt=datetime(2017, 11, 11, 0, 0),
    )
    forecast_2 = set_up_probability_cube(
        forecast_data_stack,
        thresholds,
        time=datetime(2017, 11, 11, 8, 0),
        frt=datetime(2017, 11, 11, 0, 0),
    )
    forecasts_grid = MergeCubes()([forecast_1, forecast_2])
    return forecasts_grid


@pytest.fixture
def percentile_forecast_grid():
    percentiles = [50, 90]
    np.random.seed(0)
    forecast_data = (
        np.random.uniform(low=283, high=288, size=9).astype(np.float32).reshape(3, 3)
    )
    forecast_data_stack = np.stack([forecast_data, forecast_data + 5])
    forecast = set_up_percentile_cube(
        forecast_data_stack,
        percentiles,
        time=datetime(2017, 11, 11, 4, 0),
        frt=datetime(2017, 11, 11, 0, 0),
    )
    return forecast


def test_no_threshold_coord(percentile_forecast_grid):
    # test that error is raised when the input is not a probability cube
    msg = "must be a probability forecast"
    recalibration_dict = {
        "forecast_period": [0, 1],
        "alpha": [2, 0],
        "beta": [2, 1],
        "units": "hours",
    }
    plugin = BetaRecalibrate(recalibration_dict)
    with pytest.raises(CoordinateNotFoundError, match=msg):
        plugin.process(percentile_forecast_grid.copy())


def test_no_forecast_period_coord(forecast_grid):
    # test that error is raised when the input does not contain
    # a forecast_period coordinate
    forecast_grid.remove_coord("forecast_period")
    msg = "must contain forecast_period coordinate"
    recalibration_dict = {
        "forecast_period": [0, 1],
        "alpha": [2, 0],
        "beta": [2, 1],
        "units": "hours",
    }
    plugin = BetaRecalibrate(recalibration_dict)
    with pytest.raises(CoordinateNotFoundError, match=msg):
        plugin.process(forecast_grid.copy())


def test_invalid_params(forecast_grid):
    # test that error is raised when alpha or beta parameter is invalid
    msg = "interpolated alpha and beta parameters must be > 0"
    recalibration_dict = {
        "forecast_period": [0, 1],
        "alpha": [2, 0],
        "beta": [2, 1],
        "units": "hours",
    }
    plugin = BetaRecalibrate(recalibration_dict)
    with pytest.raises(RuntimeError, match=msg):
        plugin.process(forecast_grid.copy())


def test_recalibrate(forecast_grid):
    # test recalibration
    recalibration_dict = {
        "forecast_period": [0, 1],
        "alpha": [0, 1],
        "beta": [0, 2],
        "units": "hours",
    }
    plugin = BetaRecalibrate(recalibration_dict)
    result = plugin.process(forecast_grid.copy())
    f1 = forecast_grid.extract(iris.Constraint(time=lambda cell: cell.point.hour == 4))
    f2 = forecast_grid.extract(iris.Constraint(time=lambda cell: cell.point.hour == 8))
    f1.data = beta.cdf(f1.data, 4, 8)
    f2.data = beta.cdf(f2.data, 8, 16)
    expected = MergeCubes()([f1, f2])
    assert result.coords() == expected.coords()
    assert result.attributes == expected.attributes
    np.testing.assert_almost_equal(expected.data, expected.data)


def test_params_equal_1(forecast_grid):
    # check that recalibration has no effect when alpha = beta = 1
    recalibration_dict = {
        "forecast_period": [0, 1],
        "alpha": [1, 1],
        "beta": [1, 1],
        "units": "hours",
    }
    plugin = BetaRecalibrate(recalibration_dict)
    result = plugin.process(forecast_grid.copy())

    assert result.coords() == forecast_grid.coords()
    assert result.attributes == forecast_grid.attributes
    np.testing.assert_almost_equal(result.data, forecast_grid.data)
