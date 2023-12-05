import datetime
import numpy as np

import pytest

import matplotlib.pyplot as plt
import matplotlib as mpl


class TestDatetimePlotting:
    @pytest.mark.xfail(reason="Test for acorr not written yet")
    @mpl.style.context("default")
    def test_acorr(self):
        fig, ax = plt.subplots()
        ax.acorr(...)

    @pytest.mark.xfail(reason="Test for annotate not written yet")
    @mpl.style.context("default")
    def test_annotate(self):
        fig, ax = plt.subplots()
        ax.annotate(...)

    @pytest.mark.xfail(reason="Test for arrow not written yet")
    @mpl.style.context("default")
    def test_arrow(self):
        fig, ax = plt.subplots()
        ax.arrow(...)

    @pytest.mark.xfail(reason="Test for axhline not written yet")
    @mpl.style.context("default")
    def test_axhline(self):
        fig, ax = plt.subplots()
        ax.axhline(...)

    @pytest.mark.xfail(reason="Test for axhspan not written yet")
    @mpl.style.context("default")
    def test_axhspan(self):
        fig, ax = plt.subplots()
        ax.axhspan(...)

    @pytest.mark.xfail(reason="Test for axline not written yet")
    @mpl.style.context("default")
    def test_axline(self):
        fig, ax = plt.subplots()
        ax.axline(...)

    @pytest.mark.xfail(reason="Test for axvline not written yet")
    @mpl.style.context("default")
    def test_axvline(self):
        fig, ax = plt.subplots()
        ax.axvline(...)

    @pytest.mark.xfail(reason="Test for axvspan not written yet")
    @mpl.style.context("default")
    def test_axvspan(self):
        fig, ax = plt.subplots()
        ax.axvspan(...)

    @pytest.mark.xfail(reason="Test for bar not written yet")
    @mpl.style.context("default")
    def test_bar(self):
        fig, ax = plt.subplots()
        ax.bar(...)

    @pytest.mark.xfail(reason="Test for bar_label not written yet")
    @mpl.style.context("default")
    def test_bar_label(self):
        fig, ax = plt.subplots()
        ax.bar_label(...)

    @pytest.mark.xfail(reason="Test for barbs not written yet")
    @mpl.style.context("default")
    def test_barbs(self):
        fig, ax = plt.subplots()
        ax.barbs(...)

    @mpl.style.context("default")
    def test_barh(self):
        mpl.rcParams["date.converter"] = 'concise'
        fig, (ax1, ax2) = plt.subplots(2, 1, layout='constrained')
        birth_date = np.array([datetime.datetime(2020, 4, 10),
                               datetime.datetime(2020, 5, 30),
                               datetime.datetime(2020, 10, 12),
                               datetime.datetime(2020, 11, 15)])
        year_start = datetime.datetime(2020, 1, 1)
        year_end = datetime.datetime(2020, 12, 31)
        age = [21, 53, 20, 24]
        ax1.set_xlabel('Age')
        ax1.set_ylabel('Birth Date')
        ax1.barh(birth_date, width=age, height=datetime.timedelta(days=10))
        ax2.set_xlim(left=year_start, right=year_end)
        ax2.set_xlabel('Birth Date')
        ax2.set_ylabel('Order of Birth Dates')
        ax2.barh(np.arange(4), birth_date-year_start, left=year_start)

    @pytest.mark.xfail(reason="Test for boxplot not written yet")
    @mpl.style.context("default")
    def test_boxplot(self):
        fig, ax = plt.subplots()
        ax.boxplot(...)

    @pytest.mark.xfail(reason="Test for broken_barh not written yet")
    @mpl.style.context("default")
    def test_broken_barh(self):
        fig, ax = plt.subplots()
        ax.broken_barh(...)

    @pytest.mark.xfail(reason="Test for bxp not written yet")
    @mpl.style.context("default")
    def test_bxp(self):
        fig, ax = plt.subplots()
        ax.bxp(...)

    @pytest.mark.xfail(reason="Test for clabel not written yet")
    @mpl.style.context("default")
    def test_clabel(self):
        fig, ax = plt.subplots()
        ax.clabel(...)

    @pytest.mark.xfail(reason="Test for contour not written yet")
    @mpl.style.context("default")
    def test_contour(self):
        fig, ax = plt.subplots()
        ax.contour(...)

    @pytest.mark.xfail(reason="Test for contourf not written yet")
    @mpl.style.context("default")
    def test_contourf(self):
        fig, ax = plt.subplots()
        ax.contourf(...)

    @pytest.mark.xfail(reason="Test for errorbar not written yet")
    @mpl.style.context("default")
    def test_errorbar(self):
        fig, ax = plt.subplots()
        ax.errorbar(...)

    @pytest.mark.xfail(reason="Test for eventplot not written yet")
    @mpl.style.context("default")
    def test_eventplot(self):
        fig, ax = plt.subplots()
        ax.eventplot(...)

    @pytest.mark.xfail(reason="Test for fill not written yet")
    @mpl.style.context("default")
    def test_fill(self):
        fig, ax = plt.subplots()
        ax.fill(...)

    @pytest.mark.xfail(reason="Test for fill_between not written yet")
    @mpl.style.context("default")
    def test_fill_between(self):
        fig, ax = plt.subplots()
        ax.fill_between(...)

    @pytest.mark.xfail(reason="Test for fill_betweenx not written yet")
    @mpl.style.context("default")
    def test_fill_betweenx(self):
        fig, ax = plt.subplots()
        ax.fill_betweenx(...)

    @pytest.mark.xfail(reason="Test for hexbin not written yet")
    @mpl.style.context("default")
    def test_hexbin(self):
        fig, ax = plt.subplots()
        ax.hexbin(...)

    @mpl.style.context("default")
    def test_hist(self):
        mpl.rcParams["date.converter"] = 'concise'

        start_date = datetime.datetime(2023, 10, 1)
        time_delta = datetime.timedelta(days=1)

        values1 = np.random.randint(1, 10, 30)
        values2 = np.random.randint(1, 10, 30)
        values3 = np.random.randint(1, 10, 30)

        bin_edges = [start_date + i * time_delta for i in range(31)]

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, constrained_layout=True)
        ax1.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=10,
            weights=values1
        )
        ax2.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=10,
            weights=values2
        )
        ax3.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=10,
            weights=values3
        )

        fig, (ax4, ax5, ax6) = plt.subplots(3, 1, constrained_layout=True)
        ax4.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=bin_edges,
            weights=values1
        )
        ax5.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=bin_edges,
            weights=values2
        )
        ax6.hist(
            [start_date + i * time_delta for i in range(30)],
            bins=bin_edges,
            weights=values3
        )

    @pytest.mark.xfail(reason="Test for hist2d not written yet")
    @mpl.style.context("default")
    def test_hist2d(self):
        fig, ax = plt.subplots()
        ax.hist2d(...)

    @pytest.mark.xfail(reason="Test for hlines not written yet")
    @mpl.style.context("default")
    def test_hlines(self):
        fig, ax = plt.subplots()
        ax.hlines(...)

    @pytest.mark.xfail(reason="Test for imshow not written yet")
    @mpl.style.context("default")
    def test_imshow(self):
        fig, ax = plt.subplots()
        ax.imshow(...)

    @pytest.mark.xfail(reason="Test for loglog not written yet")
    @mpl.style.context("default")
    def test_loglog(self):
        fig, ax = plt.subplots()
        ax.loglog(...)

    @pytest.mark.xfail(reason="Test for matshow not written yet")
    @mpl.style.context("default")
    def test_matshow(self):
        fig, ax = plt.subplots()
        ax.matshow(...)

    @pytest.mark.xfail(reason="Test for pcolor not written yet")
    @mpl.style.context("default")
    def test_pcolor(self):
        fig, ax = plt.subplots()
        ax.pcolor(...)

    @pytest.mark.xfail(reason="Test for pcolorfast not written yet")
    @mpl.style.context("default")
    def test_pcolorfast(self):
        fig, ax = plt.subplots()
        ax.pcolorfast(...)

    @pytest.mark.xfail(reason="Test for pcolormesh not written yet")
    @mpl.style.context("default")
    def test_pcolormesh(self):
        fig, ax = plt.subplots()
        ax.pcolormesh(...)

    @mpl.style.context("default")
    def test_plot(self):
        mpl.rcParams["date.converter"] = 'concise'
        N = 6
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, layout='constrained')
        x = np.array([datetime.datetime(2023, 9, n) for n in range(1, N)])
        ax1.plot(x, range(1, N))
        ax2.plot(range(1, N), x)
        ax3.plot(x, x)

    @mpl.style.context("default")
    def test_plot_date(self):
        mpl.rcParams["date.converter"] = "concise"
        range_threshold = 10
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, layout="constrained")

        x_dates = np.array(
            [datetime.datetime(2023, 10, delta) for delta in range(1, range_threshold)]
        )
        y_dates = np.array(
            [datetime.datetime(2023, 10, delta) for delta in range(1, range_threshold)]
        )
        x_ranges = np.array(range(1, range_threshold))
        y_ranges = np.array(range(1, range_threshold))

        ax1.plot_date(x_dates, y_dates)
        ax2.plot_date(x_dates, y_ranges)
        ax3.plot_date(x_ranges, y_dates)

    @pytest.mark.xfail(reason="Test for quiver not written yet")
    @mpl.style.context("default")
    def test_quiver(self):
        fig, ax = plt.subplots()
        ax.quiver(...)

    @pytest.mark.xfail(reason="Test for quiverkey not written yet")
    @mpl.style.context("default")
    def test_quiverkey(self):
        fig, ax = plt.subplots()
        ax.quiverkey(...)

    @pytest.mark.xfail(reason="Test for scatter not written yet")
    @mpl.style.context("default")
    def test_scatter(self):
        fig, ax = plt.subplots()
        ax.scatter(...)

    @pytest.mark.xfail(reason="Test for semilogx not written yet")
    @mpl.style.context("default")
    def test_semilogx(self):
        fig, ax = plt.subplots()
        ax.semilogx(...)

    @pytest.mark.xfail(reason="Test for semilogy not written yet")
    @mpl.style.context("default")
    def test_semilogy(self):
        fig, ax = plt.subplots()
        ax.semilogy(...)

    @pytest.mark.xfail(reason="Test for spy not written yet")
    @mpl.style.context("default")
    def test_spy(self):
        fig, ax = plt.subplots()
        ax.spy(...)

    @pytest.mark.xfail(reason="Test for stackplot not written yet")
    @mpl.style.context("default")
    def test_stackplot(self):
        fig, ax = plt.subplots()
        ax.stackplot(...)

    @pytest.mark.xfail(reason="Test for stairs not written yet")
    @mpl.style.context("default")
    def test_stairs(self):
        fig, ax = plt.subplots()
        ax.stairs(...)

    @mpl.style.context("default")
    def test_stem(self):
        mpl.rcParams["date.converter"] = "concise"

        fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, 1, layout="constrained")

        limit_value = 10
        above = datetime.datetime(2023, 9, 18)
        below = datetime.datetime(2023, 11, 18)

        x_ranges = np.arange(1, limit_value)
        y_ranges = np.arange(1, limit_value)

        x_dates = np.array(
            [datetime.datetime(2023, 10, n) for n in range(1, limit_value)]
        )
        y_dates = np.array(
            [datetime.datetime(2023, 10, n) for n in range(1, limit_value)]
        )

        ax1.stem(x_dates, y_dates, bottom=above)
        ax2.stem(x_dates, y_ranges, bottom=5)
        ax3.stem(x_ranges, y_dates, bottom=below)

        ax4.stem(x_ranges, y_dates, orientation="horizontal", bottom=above)
        ax5.stem(x_dates, y_ranges, orientation="horizontal", bottom=5)
        ax6.stem(x_ranges, y_dates, orientation="horizontal", bottom=below)

    @pytest.mark.xfail(reason="Test for step not written yet")
    @mpl.style.context("default")
    def test_step(self):
        fig, ax = plt.subplots()
        ax.step(...)

    @pytest.mark.xfail(reason="Test for streamplot not written yet")
    @mpl.style.context("default")
    def test_streamplot(self):
        fig, ax = plt.subplots()
        ax.streamplot(...)

    @pytest.mark.xfail(reason="Test for text not written yet")
    @mpl.style.context("default")
    def test_text(self):
        fig, ax = plt.subplots()
        ax.text(...)

    @pytest.mark.xfail(reason="Test for tricontour not written yet")
    @mpl.style.context("default")
    def test_tricontour(self):
        fig, ax = plt.subplots()
        ax.tricontour(...)

    @pytest.mark.xfail(reason="Test for tricontourf not written yet")
    @mpl.style.context("default")
    def test_tricontourf(self):
        fig, ax = plt.subplots()
        ax.tricontourf(...)

    @pytest.mark.xfail(reason="Test for tripcolor not written yet")
    @mpl.style.context("default")
    def test_tripcolor(self):
        fig, ax = plt.subplots()
        ax.tripcolor(...)

    @pytest.mark.xfail(reason="Test for triplot not written yet")
    @mpl.style.context("default")
    def test_triplot(self):
        fig, ax = plt.subplots()
        ax.triplot(...)

    @pytest.mark.xfail(reason="Test for violin not written yet")
    @mpl.style.context("default")
    def test_violin(self):
        fig, ax = plt.subplots()
        ax.violin(...)

    @pytest.mark.xfail(reason="Test for violinplot not written yet")
    @mpl.style.context("default")
    def test_violinplot(self):
        fig, ax = plt.subplots()
        ax.violinplot(...)

    @pytest.mark.xfail(reason="Test for vlines not written yet")
    @mpl.style.context("default")
    def test_vlines(self):
        fig, ax = plt.subplots()
        ax.vlines(...)

    @pytest.mark.xfail(reason="Test for xcorr not written yet")
    @mpl.style.context("default")
    def test_xcorr(self):
        fig, ax = plt.subplots()
        ax.xcorr(...)
