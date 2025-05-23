# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of 'IMPROVER' and is released under the BSD 3-Clause license.
# See LICENSE in the root of the repository for full licensing details.
"""Tests for the apply-beta-calibration CLI."""

import pytest

from . import acceptance as acc

pytestmark = [pytest.mark.acc, acc.skip_if_kgo_missing]
CLI = acc.cli_name_with_dashes(__file__)
run_cli = acc.run_cli(CLI)


def test_calibration(tmp_path):
    """
    Test recalibration of a forecast using beta distribution.
    """
    kgo_dir = acc.kgo_root() / "apply-beta-recalibration"
    kgo_path = kgo_dir / "kgo.nc"
    forecast_path = kgo_dir / "forecast.nc"
    config_path = kgo_dir / "config.json"
    output_path = tmp_path / "output.nc"
    args = [forecast_path, config_path, "--output", output_path]
    run_cli(args)
    acc.compare(output_path, kgo_path)
