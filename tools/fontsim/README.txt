fontsim - an APPROXIMATE look at the GRFNT fonts of ATEXT (EXPERIMENTAL)

fontsim.py   the glyphs of the C47 TTFs (rasterized with the C47 tool ttf2RasterFonts into
             /tmp/fnt/raster.c); fonts 10 tiny, 20 standard, 30 numeric, 40 numeric bold are the real
             bitmaps. 21 compressed, 22 bold, 23 enlarged, 31, 32 (half size), 41 are GUESSES from the
             C43 display code - check them against a SNAP of Jaco's GRFNTS on the calculator.
fs_demo.py   GRFNTS (Jaco Mostert) as the simulation draws it -> docs/grfnt/grfnts_sim.png
fs_chart.py  the CHART panel in 20 (now), 21, 10, 32, 22, with star numbers -> docs/grfnt/chart_fonts.png
fs_prog.py   extras/FNTCHT.txt: three CHART rows in 21, 32, 10, 20 at the simulated places, to SNAP
             on the calculator and compare with docs/grfnt/fntcht_sim.png
