/* -*- mode: c++; c-basic-offset: 4 -*- */

/* _backend_agg.h
*/

#ifndef __BACKEND_AGG_H__
#define __BACKEND_AGG_H__

#include <vector>

#include "agg_alpha_mask_u8.h"
#include "agg_conv_curve.h"
#include "agg_conv_dash.h"
#include "agg_conv_stroke.h"
#include "agg_image_accessors.h"
#include "agg_pixfmt_amask_adaptor.h"
#include "agg_pixfmt_gray.h"
#include "agg_pixfmt_rgba.h"
#include "agg_rasterizer_scanline_aa.h"
#include "agg_renderer_base.h"
#include "agg_renderer_scanline.h"
#include "agg_rendering_buffer.h"
#include "agg_scanline_bin.h"
#include "agg_scanline_p.h"
#include "agg_scanline_storage_aa.h"
#include "agg_scanline_storage_bin.h"
#include "agg_scanline_u.h"
#include "agg_span_allocator.h"
#include "agg_span_converter.h"
#include "agg_span_gouraud_rgba.h"
#include "agg_span_image_filter_gray.h"
#include "agg_span_image_filter_rgba.h"
#include "agg_span_interpolator_linear.h"
#include "agg_span_pattern_rgba.h"
#include "util/agg_color_conv_rgb8.h"

#include "_backend_agg_basic_types.h"
#include "path_converters.h"
#include "array.h"

typedef agg::pixfmt_rgba32_plain pixfmt;
typedef agg::renderer_base<pixfmt> renderer_base;
typedef agg::renderer_scanline_aa_solid<renderer_base> renderer_aa;
typedef agg::renderer_scanline_bin_solid<renderer_base> renderer_bin;
typedef agg::rasterizer_scanline_aa<agg::rasterizer_sl_clip_dbl> rasterizer;

typedef agg::scanline_p8 scanline_p8;
typedef agg::scanline_bin scanline_bin;
typedef agg::amask_no_clip_gray8 alpha_mask_type;
typedef agg::scanline_u8_am<alpha_mask_type> scanline_am;

typedef agg::renderer_base<agg::pixfmt_gray8> renderer_base_alpha_mask_type;
typedef agg::renderer_scanline_aa_solid<renderer_base_alpha_mask_type> renderer_alpha_mask_type;

// a helper class to pass agg::buffer objects around.  agg::buffer is
// a class in the swig wrapper
class BufferRegion
{
  public:
    BufferRegion(const agg::rect_i &r) : rect(r)
    {
        width = r.x2 - r.x1;
        height = r.y2 - r.y1;
        stride = width * 4;
        data = new agg::int8u[stride * height];
    }

    virtual ~BufferRegion()
    {
        delete[] data;
    };

    agg::int8u *get_data()
    {
        return data;
    }

    agg::rect_i &get_rect()
    {
        return rect;
    }

    int get_width()
    {
        return width;
    }

    int get_height()
    {
        return height;
    }

    int get_stride()
    {
        return stride;
    }

    void to_string_argb(uint8_t *buf);

  private:
    agg::int8u *data;
    agg::rect_i rect;
    int width;
    int height;
    int stride;

  private:
    // prevent copying
    BufferRegion(const BufferRegion &);
    BufferRegion &operator=(const BufferRegion &);
};

#define MARKER_CACHE_SIZE 512

// the renderer
class RendererAgg
{
    /* TODO: Remove facepair_t */
    typedef std::pair<bool, agg::rgba> facepair_t;

  public:
    RendererAgg(unsigned int width, unsigned int height, double dpi);

    virtual ~RendererAgg();

    unsigned int get_width()
    {
        return width;
    }

    unsigned int get_height()
    {
        return height;
    }

    template <class PathIterator>
    void draw_path(GCAgg &gc, PathIterator &path, agg::trans_affine &trans, agg::rgba &color);

    template <class PathIterator>
    void draw_markers(GCAgg &gc,
                      PathIterator &marker_path,
                      agg::trans_affine &marker_path_trans,
                      PathIterator &path,
                      agg::trans_affine &trans,
                      agg::rgba face);

    template <class ImageArray>
    void draw_text_image(GCAgg &gc, ImageArray &image, int x, int y, double angle);

    template <class ImageArray>
    void draw_image(GCAgg &gc,
                    double x,
                    double y,
                    ImageArray &image,
                    double w,
                    double h,
                    agg::trans_affine trans,
                    bool resize);

    template <class PathGenerator,
              class TransformArray,
              class OffsetArray,
              class ColorArray,
              class LineWidthArray,
              class AntialiasedArray>
    void draw_path_collection(GCAgg &gc,
                              agg::trans_affine &master_transform,
                              PathGenerator &path,
                              TransformArray &transforms,
                              OffsetArray &offsets,
                              agg::trans_affine &offset_trans,
                              ColorArray &facecolors,
                              ColorArray &edgecolors,
                              LineWidthArray &linewidths,
                              DashesVector &linestyles,
                              AntialiasedArray &antialiaseds,
                              e_offset_position offset_position);

    template <class CoordinateArray, class OffsetArray, class ColorArray>
    void draw_quad_mesh(GCAgg &gc,
                        agg::trans_affine &master_transform,
                        size_t mesh_width,
                        size_t mesh_height,
                        CoordinateArray &coordinates,
                        OffsetArray &offsets,
                        agg::trans_affine &offset_trans,
                        ColorArray &facecolors,
                        bool antialiased,
                        ColorArray &edgecolors);

    template <class PointArray, class ColorArray>
    void draw_gouraud_triangle(GCAgg &gc,
                               PointArray &points,
                               ColorArray &colors,
                               agg::trans_affine &trans);

    template <class PointArray, class ColorArray>
    void draw_gouraud_triangles(GCAgg &gc,
                                PointArray &points,
                                ColorArray &colors,
                                agg::trans_affine &trans);

    void tostring_rgb(uint8_t *buf);
    void tostring_argb(uint8_t *buf);
    void tostring_bgra(uint8_t *buf);
    agg::rect_i get_content_extents();
    void clear();

    BufferRegion *copy_from_bbox(agg::rect_d in_rect);
    void restore_region(BufferRegion &reg);
    void restore_region(BufferRegion &region, int x, int y, int xx1, int yy1, int xx2, int yy2);

    unsigned int width, height;
    double dpi;
    size_t NUMBYTES; // the number of bytes in buffer

    agg::int8u *pixBuffer;
    agg::rendering_buffer renderingBuffer;

    agg::int8u *alphaBuffer;
    agg::rendering_buffer alphaMaskRenderingBuffer;
    alpha_mask_type alphaMask;
    agg::pixfmt_gray8 pixfmtAlphaMask;
    renderer_base_alpha_mask_type rendererBaseAlphaMask;
    renderer_alpha_mask_type rendererAlphaMask;
    scanline_am scanlineAlphaMask;

    scanline_p8 slineP8;
    scanline_bin slineBin;
    pixfmt pixFmt;
    renderer_base rendererBase;
    renderer_aa rendererAA;
    renderer_bin rendererBin;
    rasterizer theRasterizer;

    void *lastclippath;
    agg::trans_affine lastclippath_transform;

    static const size_t HATCH_SIZE = 72;
    agg::int8u hatchBuffer[HATCH_SIZE * HATCH_SIZE * 4];
    agg::rendering_buffer hatchRenderingBuffer;

    agg::rgba _fill_color;

  protected:
    inline double points_to_pixels(double points)
    {
        return points * dpi / 72.0;
    }

    template <class R>
    void set_clipbox(const agg::rect_d &cliprect, R &rasterizer);

    bool render_clippath(py::PathIterator &clippath, const agg::trans_affine &clippath_trans);

    template <class PathIteratorType>
    void _draw_path(PathIteratorType &path, bool has_clippath, const facepair_t &face, GCAgg &gc);

    template <class PathIterator,
              class PathGenerator,
              class TransformArray,
              class OffsetArray,
              class ColorArray,
              class LineWidthArray,
              class AntialiasedArray>
    void _draw_path_collection_generic(GCAgg &gc,
                                       agg::trans_affine master_transform,
                                       const agg::rect_d &cliprect,
                                       PathIterator &clippath,
                                       const agg::trans_affine &clippath_trans,
                                       PathGenerator &path_generator,
                                       TransformArray &transforms,
                                       OffsetArray &offsets,
                                       const agg::trans_affine &offset_trans,
                                       ColorArray &facecolors,
                                       ColorArray &edgecolors,
                                       LineWidthArray &linewidths,
                                       DashesVector &linestyles,
                                       AntialiasedArray &antialiaseds,
                                       e_offset_position offset_position,
                                       int check_snap,
                                       int has_curves);

    template <class PointArray, class ColorArray>
    void _draw_gouraud_triangle(PointArray &points,
                                ColorArray &colors,
                                agg::trans_affine trans,
                                bool has_clippath);

  private:
    void create_alpha_buffers();

    // prevent copying
    RendererAgg(const RendererAgg &);
    RendererAgg &operator=(const RendererAgg &);
};

/***************************************************************************
 * Implementation
 */

template <class path_t>
inline void
RendererAgg::_draw_path(path_t &path, bool has_clippath, const facepair_t &face, GCAgg &gc)
{
    typedef agg::conv_stroke<path_t> stroke_t;
    typedef agg::conv_dash<path_t> dash_t;
    typedef agg::conv_stroke<dash_t> stroke_dash_t;
    typedef agg::pixfmt_amask_adaptor<pixfmt, alpha_mask_type> pixfmt_amask_type;
    typedef agg::renderer_base<pixfmt_amask_type> amask_ren_type;
    typedef agg::renderer_scanline_aa_solid<amask_ren_type> amask_aa_renderer_type;
    typedef agg::renderer_scanline_bin_solid<amask_ren_type> amask_bin_renderer_type;

    // Render face
    if (face.first) {
        theRasterizer.add_path(path);

        if (gc.isaa) {
            if (has_clippath) {
                pixfmt_amask_type pfa(pixFmt, alphaMask);
                amask_ren_type r(pfa);
                amask_aa_renderer_type ren(r);
                ren.color(face.second);
                agg::render_scanlines(theRasterizer, scanlineAlphaMask, ren);
            } else {
                rendererAA.color(face.second);
                agg::render_scanlines(theRasterizer, slineP8, rendererAA);
            }
        } else {
            if (has_clippath) {
                pixfmt_amask_type pfa(pixFmt, alphaMask);
                amask_ren_type r(pfa);
                amask_bin_renderer_type ren(r);
                ren.color(face.second);
                agg::render_scanlines(theRasterizer, scanlineAlphaMask, ren);
            } else {
                rendererBin.color(face.second);
                agg::render_scanlines(theRasterizer, slineP8, rendererBin);
            }
        }
    }

    // Render hatch
    if (gc.has_hatchpath()) {
        // Reset any clipping that may be in effect, since we'll be
        // drawing the hatch in a scratch buffer at origin (0, 0)
        theRasterizer.reset_clipping();
        rendererBase.reset_clipping(true);

        // Create and transform the path
        typedef agg::conv_transform<py::PathIterator> hatch_path_trans_t;
        typedef agg::conv_curve<hatch_path_trans_t> hatch_path_curve_t;
        typedef agg::conv_stroke<hatch_path_curve_t> hatch_path_stroke_t;

        py::PathIterator hatch_path(gc.hatchpath);
        agg::trans_affine hatch_trans;
        hatch_trans *= agg::trans_affine_scaling(1.0, -1.0);
        hatch_trans *= agg::trans_affine_translation(0.0, 1.0);
        hatch_trans *= agg::trans_affine_scaling(HATCH_SIZE, HATCH_SIZE);
        hatch_path_trans_t hatch_path_trans(hatch_path, hatch_trans);
        hatch_path_curve_t hatch_path_curve(hatch_path_trans);
        hatch_path_stroke_t hatch_path_stroke(hatch_path_curve);
        hatch_path_stroke.width(1.0);
        hatch_path_stroke.line_cap(agg::square_cap);

        // Render the path into the hatch buffer
        pixfmt hatch_img_pixf(hatchRenderingBuffer);
        renderer_base rb(hatch_img_pixf);
        renderer_aa rs(rb);
        rb.clear(_fill_color);
        rs.color(gc.color);

        theRasterizer.add_path(hatch_path_curve);
        agg::render_scanlines(theRasterizer, slineP8, rs);
        theRasterizer.add_path(hatch_path_stroke);
        agg::render_scanlines(theRasterizer, slineP8, rs);

        // Put clipping back on, if originally set on entry to this
        // function
        set_clipbox(gc.cliprect, theRasterizer);
        if (has_clippath) {
            render_clippath(gc.clippath.path, gc.clippath.trans);
        }

        // Transfer the hatch to the main image buffer
        typedef agg::image_accessor_wrap<pixfmt,
                                         agg::wrap_mode_repeat_auto_pow2,
                                         agg::wrap_mode_repeat_auto_pow2> img_source_type;
        typedef agg::span_pattern_rgba<img_source_type> span_gen_type;
        agg::span_allocator<agg::rgba8> sa;
        img_source_type img_src(hatch_img_pixf);
        span_gen_type sg(img_src, 0, 0);
        theRasterizer.add_path(path);

        if (has_clippath) {
            pixfmt_amask_type pfa(pixFmt, alphaMask);
            amask_ren_type ren(pfa);
            agg::render_scanlines_aa(theRasterizer, slineP8, ren, sa, sg);
        } else {
            agg::render_scanlines_aa(theRasterizer, slineP8, rendererBase, sa, sg);
        }
    }

    // Render stroke
    if (gc.linewidth != 0.0) {
        double linewidth = points_to_pixels(gc.linewidth);
        if (!gc.isaa) {
            linewidth = (linewidth < 0.5) ? 0.5 : mpl_round(linewidth);
        }
        if (gc.dashes.size() == 0) {
            stroke_t stroke(path);
            stroke.width(points_to_pixels(gc.linewidth));
            stroke.line_cap(gc.cap);
            stroke.line_join(gc.join);
            theRasterizer.add_path(stroke);
        } else {
            dash_t dash(path);
            gc.dashes.dash_to_stroke(dash, dpi, gc.isaa);
            stroke_dash_t stroke(dash);
            stroke.line_cap(gc.cap);
            stroke.line_join(gc.join);
            stroke.width(linewidth);
            theRasterizer.add_path(stroke);
        }

        if (gc.isaa) {
            if (has_clippath) {
                pixfmt_amask_type pfa(pixFmt, alphaMask);
                amask_ren_type r(pfa);
                amask_aa_renderer_type ren(r);
                ren.color(gc.color);
                agg::render_scanlines(theRasterizer, scanlineAlphaMask, ren);
            } else {
                rendererAA.color(gc.color);
                agg::render_scanlines(theRasterizer, slineP8, rendererAA);
            }
        } else {
            if (has_clippath) {
                pixfmt_amask_type pfa(pixFmt, alphaMask);
                amask_ren_type r(pfa);
                amask_bin_renderer_type ren(r);
                ren.color(gc.color);
                agg::render_scanlines(theRasterizer, scanlineAlphaMask, ren);
            } else {
                rendererBin.color(gc.color);
                agg::render_scanlines(theRasterizer, slineBin, rendererBin);
            }
        }
    }
}

template <class PathIterator>
inline void
RendererAgg::draw_path(GCAgg &gc, PathIterator &path, agg::trans_affine &trans, agg::rgba &color)
{
    typedef agg::conv_transform<py::PathIterator> transformed_path_t;
    typedef PathNanRemover<transformed_path_t> nan_removed_t;
    typedef PathClipper<nan_removed_t> clipped_t;
    typedef PathSnapper<clipped_t> snapped_t;
    typedef PathSimplifier<snapped_t> simplify_t;
    typedef agg::conv_curve<simplify_t> curve_t;
    typedef Sketch<curve_t> sketch_t;

    facepair_t face(color.a != 0.0, color);

    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(gc.cliprect, theRasterizer);
    bool has_clippath = render_clippath(gc.clippath.path, gc.clippath.trans);

    trans *= agg::trans_affine_scaling(1.0, -1.0);
    trans *= agg::trans_affine_translation(0.0, (double)height);
    bool clip = !face.first && gc.has_hatchpath() && !path.has_curves();
    bool simplify = path.should_simplify() && clip;
    double snapping_linewidth = points_to_pixels(gc.linewidth);
    if (gc.color.a == 0.0) {
        snapping_linewidth = 0.0;
    }

    transformed_path_t tpath(path, trans);
    nan_removed_t nan_removed(tpath, true, path.has_curves());
    clipped_t clipped(nan_removed, clip, width, height);
    snapped_t snapped(clipped, gc.snap_mode, path.total_vertices(), snapping_linewidth);
    simplify_t simplified(snapped, simplify, path.simplify_threshold());
    curve_t curve(simplified);
    sketch_t sketch(curve, gc.sketch.scale, gc.sketch.length, gc.sketch.randomness);

    _draw_path(sketch, has_clippath, face, gc);
}

template <class PathIterator>
inline void RendererAgg::draw_markers(GCAgg &gc,
                                      PathIterator &marker_path,
                                      agg::trans_affine &marker_trans,
                                      PathIterator &path,
                                      agg::trans_affine &trans,
                                      agg::rgba color)
{
    typedef agg::conv_transform<py::PathIterator> transformed_path_t;
    typedef PathSnapper<transformed_path_t> snap_t;
    typedef agg::conv_curve<snap_t> curve_t;
    typedef agg::conv_stroke<curve_t> stroke_t;
    typedef agg::pixfmt_amask_adaptor<pixfmt, alpha_mask_type> pixfmt_amask_type;
    typedef agg::renderer_base<pixfmt_amask_type> amask_ren_type;
    typedef agg::renderer_scanline_aa_solid<amask_ren_type> amask_aa_renderer_type;

    // Deal with the difference in y-axis direction
    marker_trans *= agg::trans_affine_scaling(1.0, -1.0);
    trans *= agg::trans_affine_scaling(1.0, -1.0);
    trans *= agg::trans_affine_translation(0.5, (double)height + 0.5);

    transformed_path_t marker_path_transformed(marker_path, marker_trans);
    snap_t marker_path_snapped(marker_path_transformed,
                               gc.snap_mode,
                               marker_path.total_vertices(),
                               points_to_pixels(gc.linewidth));
    curve_t marker_path_curve(marker_path_snapped);

    transformed_path_t path_transformed(path, trans);
    snap_t path_snapped(path_transformed, SNAP_FALSE, path.total_vertices(), 0.0);
    curve_t path_curve(path_snapped);
    path_curve.rewind(0);

    facepair_t face(color.a != 0.0, color);

    // maxim's suggestions for cached scanlines
    agg::scanline_storage_aa8 scanlines;
    theRasterizer.reset();
    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);

    agg::int8u staticFillCache[MARKER_CACHE_SIZE];
    agg::int8u staticStrokeCache[MARKER_CACHE_SIZE];
    agg::int8u *fillCache = staticFillCache;
    agg::int8u *strokeCache = staticStrokeCache;

    try
    {
        unsigned fillSize = 0;
        if (face.first) {
            theRasterizer.add_path(marker_path_curve);
            agg::render_scanlines(theRasterizer, slineP8, scanlines);
            fillSize = scanlines.byte_size();
            if (fillSize >= MARKER_CACHE_SIZE) {
                fillCache = new agg::int8u[fillSize];
            }
            scanlines.serialize(fillCache);
        }

        stroke_t stroke(marker_path_curve);
        stroke.width(points_to_pixels(gc.linewidth));
        stroke.line_cap(gc.cap);
        stroke.line_join(gc.join);
        theRasterizer.reset();
        theRasterizer.add_path(stroke);
        agg::render_scanlines(theRasterizer, slineP8, scanlines);
        unsigned strokeSize = scanlines.byte_size();
        if (strokeSize >= MARKER_CACHE_SIZE) {
            strokeCache = new agg::int8u[strokeSize];
        }
        scanlines.serialize(strokeCache);

        theRasterizer.reset_clipping();
        rendererBase.reset_clipping(true);
        set_clipbox(gc.cliprect, rendererBase);
        bool has_clippath = render_clippath(gc.clippath.path, gc.clippath.trans);

        double x, y;

        agg::serialized_scanlines_adaptor_aa8 sa;
        agg::serialized_scanlines_adaptor_aa8::embedded_scanline sl;

        agg::rect_d clipping_rect(-1.0 - scanlines.max_x(),
                                  -1.0 - scanlines.max_y(),
                                  1.0 + width - scanlines.min_x(),
                                  1.0 + height - scanlines.min_y());

        if (has_clippath) {
            while (path_curve.vertex(&x, &y) != agg::path_cmd_stop) {
                if (MPL_notisfinite64(x) || MPL_notisfinite64(y)) {
                    continue;
                }

                /* These values are correctly snapped above -- so we don't want
                   to round here, we really only want to truncate */
                x = floor(x);
                y = floor(y);

                // Cull points outside the boundary of the image.
                // Values that are too large may overflow and create
                // segfaults.
                // http://sourceforge.net/tracker/?func=detail&aid=2865490&group_id=80706&atid=560720
                if (!clipping_rect.hit_test(x, y)) {
                    continue;
                }

                pixfmt_amask_type pfa(pixFmt, alphaMask);
                amask_ren_type r(pfa);
                amask_aa_renderer_type ren(r);

                if (face.first) {
                    ren.color(face.second);
                    sa.init(fillCache, fillSize, x, y);
                    agg::render_scanlines(sa, sl, ren);
                }
                ren.color(gc.color);
                sa.init(strokeCache, strokeSize, x, y);
                agg::render_scanlines(sa, sl, ren);
            }
        } else {
            while (path_curve.vertex(&x, &y) != agg::path_cmd_stop) {
                if (MPL_notisfinite64(x) || MPL_notisfinite64(y)) {
                    continue;
                }

                /* These values are correctly snapped above -- so we don't want
                   to round here, we really only want to truncate */
                x = floor(x);
                y = floor(y);

                // Cull points outside the boundary of the image.
                // Values that are too large may overflow and create
                // segfaults.
                // http://sourceforge.net/tracker/?func=detail&aid=2865490&group_id=80706&atid=560720
                if (!clipping_rect.hit_test(x, y)) {
                    continue;
                }

                if (face.first) {
                    rendererAA.color(face.second);
                    sa.init(fillCache, fillSize, x, y);
                    agg::render_scanlines(sa, sl, rendererAA);
                }

                rendererAA.color(gc.color);
                sa.init(strokeCache, strokeSize, x, y);
                agg::render_scanlines(sa, sl, rendererAA);
            }
        }
    }
    catch (...)
    {
        if (fillCache != staticFillCache)
            delete[] fillCache;
        if (strokeCache != staticStrokeCache)
            delete[] strokeCache;
        theRasterizer.reset_clipping();
        rendererBase.reset_clipping(true);
        throw;
    }

    if (fillCache != staticFillCache)
        delete[] fillCache;
    if (strokeCache != staticStrokeCache)
        delete[] strokeCache;

    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
}

/**
 * This is a custom span generator that converts spans in the
 * 8-bit inverted greyscale font buffer to rgba that agg can use.
 */
template <class ChildGenerator>
class font_to_rgba
{
  public:
    typedef ChildGenerator child_type;
    typedef agg::rgba8 color_type;
    typedef typename child_type::color_type child_color_type;
    typedef agg::span_allocator<child_color_type> span_alloc_type;

  private:
    child_type *_gen;
    color_type _color;
    span_alloc_type _allocator;

  public:
    font_to_rgba(child_type *gen, color_type color) : _gen(gen), _color(color)
    {
    }

    inline void generate(color_type *output_span, int x, int y, unsigned len)
    {
        _allocator.allocate(len);
        child_color_type *input_span = _allocator.span();
        _gen->generate(input_span, x, y, len);

        do {
            *output_span = _color;
            output_span->a = ((unsigned int)_color.a * (unsigned int)input_span->v) >> 8;
            ++output_span;
            ++input_span;
        } while (--len);
    }

    void prepare()
    {
        _gen->prepare();
    }
};

template <class ImageArray>
inline void RendererAgg::draw_text_image(GCAgg &gc, ImageArray &image, int x, int y, double angle)
{
    typedef agg::span_allocator<agg::rgba8> color_span_alloc_type;
    typedef agg::span_interpolator_linear<> interpolator_type;
    typedef agg::image_accessor_clip<agg::pixfmt_gray8> image_accessor_type;
    typedef agg::span_image_filter_gray<image_accessor_type, interpolator_type> image_span_gen_type;
    typedef font_to_rgba<image_span_gen_type> span_gen_type;
    typedef agg::renderer_scanline_aa<renderer_base, color_span_alloc_type, span_gen_type>
    renderer_type;

    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(gc.cliprect, theRasterizer);

    agg::rendering_buffer srcbuf(
        image.data(), (unsigned)image.dim(1), (unsigned)image.dim(0), (unsigned)image.dim(1));
    agg::pixfmt_gray8 pixf_img(srcbuf);

    agg::trans_affine mtx;
    mtx *= agg::trans_affine_translation(0, -image.dim(0));
    mtx *= agg::trans_affine_rotation(-angle * agg::pi / 180.0);
    mtx *= agg::trans_affine_translation(x, y);

    agg::path_storage rect;
    rect.move_to(0, 0);
    rect.line_to(image.dim(1), 0);
    rect.line_to(image.dim(1), image.dim(0));
    rect.line_to(0, image.dim(0));
    rect.line_to(0, 0);
    agg::conv_transform<agg::path_storage> rect2(rect, mtx);

    agg::trans_affine inv_mtx(mtx);
    inv_mtx.invert();

    agg::image_filter_lut filter;
    filter.calculate(agg::image_filter_spline36());
    interpolator_type interpolator(inv_mtx);
    color_span_alloc_type sa;
    image_accessor_type ia(pixf_img, 0);
    image_span_gen_type image_span_generator(ia, interpolator, filter);
    span_gen_type output_span_generator(&image_span_generator, gc.color);
    renderer_type ri(rendererBase, sa, output_span_generator);

    theRasterizer.add_path(rect2);
    agg::render_scanlines(theRasterizer, slineP8, ri);
}

class span_conv_alpha
{
  public:
    typedef agg::rgba8 color_type;

    double m_alpha;

    span_conv_alpha(double alpha) : m_alpha(alpha)
    {
    }

    void prepare()
    {
    }
    void generate(color_type *span, int x, int y, unsigned len) const
    {
        do {
            span->a = (agg::int8u)((double)span->a * m_alpha);
            ++span;
        } while (--len);
    }
};

template <class ImageArray>
inline void RendererAgg::draw_image(GCAgg &gc,
                                    double x,
                                    double y,
                                    ImageArray &image,
                                    double w,
                                    double h,
                                    agg::trans_affine trans,
                                    bool resize)
{
    double alpha = gc.alpha;

    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(gc.cliprect, theRasterizer);
    bool has_clippath = render_clippath(gc.clippath.path, gc.clippath.trans);

    agg::rendering_buffer buffer;
    buffer.attach(
        image.data(), (unsigned)image.dim(1), (unsigned)image.dim(0), -(int)image.dim(1) * 4);
    pixfmt pixf(buffer);

    if (resize | has_clippath) {
        agg::trans_affine mtx;
        agg::path_storage rect;

        if (resize) {
            mtx *= agg::trans_affine_scaling(1, -1);
            mtx *= agg::trans_affine_translation(0, image.dim(0));
            mtx *= agg::trans_affine_scaling(w / (image.dim(1)), h / (image.dim(0)));
            mtx *= agg::trans_affine_translation(x, y);
            mtx *= trans;
            mtx *= agg::trans_affine_scaling(1.0, -1.0);
            mtx *= agg::trans_affine_translation(0.0, (double)height);
        } else {
            mtx *= agg::trans_affine_translation((int)x, (int)(height - (y + image.dim(0))));
        }

        rect.move_to(0, 0);
        rect.line_to(image.dim(1), 0);
        rect.line_to(image.dim(1), image.dim(0));
        rect.line_to(0, image.dim(0));
        rect.line_to(0, 0);

        agg::conv_transform<agg::path_storage> rect2(rect, mtx);

        agg::trans_affine inv_mtx(mtx);
        inv_mtx.invert();

        typedef agg::span_allocator<agg::rgba8> color_span_alloc_type;
        typedef agg::image_accessor_clip<agg::pixfmt_rgba32_plain> image_accessor_type;
        typedef agg::span_interpolator_linear<> interpolator_type;
        typedef agg::span_image_filter_rgba_nn<image_accessor_type, interpolator_type>
        image_span_gen_type;
        typedef agg::span_converter<image_span_gen_type, span_conv_alpha> span_conv;

        color_span_alloc_type sa;
        image_accessor_type ia(pixf, agg::rgba8(0, 0, 0, 0));
        interpolator_type interpolator(inv_mtx);
        image_span_gen_type image_span_generator(ia, interpolator);
        span_conv_alpha conv_alpha(alpha);
        span_conv spans(image_span_generator, conv_alpha);

        if (has_clippath) {
            typedef agg::pixfmt_amask_adaptor<pixfmt, alpha_mask_type> pixfmt_amask_type;
            typedef agg::renderer_base<pixfmt_amask_type> amask_ren_type;
            typedef agg::renderer_scanline_aa<amask_ren_type, color_span_alloc_type, span_conv>
            renderer_type_alpha;

            pixfmt_amask_type pfa(pixFmt, alphaMask);
            amask_ren_type r(pfa);
            renderer_type_alpha ri(r, sa, spans);

            theRasterizer.add_path(rect2);
            agg::render_scanlines(theRasterizer, scanlineAlphaMask, ri);
        } else {
            typedef agg::renderer_base<pixfmt> ren_type;
            typedef agg::renderer_scanline_aa<ren_type, color_span_alloc_type, span_conv>
            renderer_type;

            ren_type r(pixFmt);
            renderer_type ri(r, sa, spans);

            theRasterizer.add_path(rect2);
            agg::render_scanlines(theRasterizer, slineP8, ri);
        }

    } else {
        set_clipbox(gc.cliprect, rendererBase);
        rendererBase.blend_from(
            pixf, 0, (int)x, (int)(height - (y + image.dim(0))), (agg::int8u)(alpha * 255));
    }

    rendererBase.reset_clipping(true);
}

template <class PathIterator,
          class PathGenerator,
          class TransformArray,
          class OffsetArray,
          class ColorArray,
          class LineWidthArray,
          class AntialiasedArray>
inline void RendererAgg::_draw_path_collection_generic(GCAgg &gc,
                                                       agg::trans_affine master_transform,
                                                       const agg::rect_d &cliprect,
                                                       PathIterator &clippath,
                                                       const agg::trans_affine &clippath_trans,
                                                       PathGenerator &path_generator,
                                                       TransformArray &transforms,
                                                       OffsetArray &offsets,
                                                       const agg::trans_affine &offset_trans,
                                                       ColorArray &facecolors,
                                                       ColorArray &edgecolors,
                                                       LineWidthArray &linewidths,
                                                       DashesVector &linestyles,
                                                       AntialiasedArray &antialiaseds,
                                                       e_offset_position offset_position,
                                                       int check_snap,
                                                       int has_curves)
{
    typedef agg::conv_transform<typename PathGenerator::path_iterator> transformed_path_t;
    typedef PathNanRemover<transformed_path_t> nan_removed_t;
    typedef PathClipper<nan_removed_t> clipped_t;
    typedef PathSnapper<clipped_t> snapped_t;
    typedef agg::conv_curve<snapped_t> snapped_curve_t;
    typedef agg::conv_curve<clipped_t> curve_t;

    if (offsets.dim(0) != 0 && offsets.dim(1) != 2) {
        throw "Offsets array must be Nx2 or empty";
    }

    if (facecolors.dim(0) != 0 && facecolors.dim(1) != 4) {
        throw "Facecolors array must be a Nx4 array or empty";
    }

    if (edgecolors.dim(0) != 0 && edgecolors.dim(1) != 4) {
        throw "Edgecolors array must by Nx4 or empty";
    }

    if (transforms.dim(0) != 0 && (transforms.dim(1) != 3 || transforms.dim(2) != 3)) {
        throw "Transforms array must by Nx3x3 or empty";
    }

    size_t Npaths = path_generator.num_paths();
    size_t Noffsets = offsets.size();
    size_t N = std::max(Npaths, Noffsets);

    size_t Ntransforms = transforms.size();
    size_t Nfacecolors = facecolors.size();
    size_t Nedgecolors = edgecolors.size();
    size_t Nlinewidths = linewidths.size();
    size_t Nlinestyles = std::min(linestyles.size(), N);
    size_t Naa = antialiaseds.size();

    if ((Nfacecolors == 0 && Nedgecolors == 0) || Npaths == 0) {
        return;
    }

    // Handle any clipping globally
    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(cliprect, theRasterizer);
    bool has_clippath = render_clippath(clippath, clippath_trans);

    // Set some defaults, assuming no face or edge
    gc.linewidth = 0.0;
    facepair_t face;
    face.first = Nfacecolors != 0;
    agg::trans_affine trans;

    for (int i = 0; i < (int)N; ++i) {
        typename PathGenerator::path_iterator path = path_generator(i);

        if (Ntransforms) {
            typename TransformArray::sub_t subtrans = transforms[i % Ntransforms];
            trans = agg::trans_affine(subtrans(0, 0),
                                      subtrans(1, 0),
                                      subtrans(0, 1),
                                      subtrans(1, 1),
                                      subtrans(0, 2),
                                      subtrans(1, 2));
        } else {
            trans = master_transform;
        }

        if (Noffsets) {
            double xo = offsets(i % Noffsets, 0);
            double yo = offsets(i % Noffsets, 1);
            offset_trans.transform(&xo, &yo);
            if (offset_position == OFFSET_POSITION_DATA) {
                trans = agg::trans_affine_translation(xo, yo) * trans;
            } else {
                trans *= agg::trans_affine_translation(xo, yo);
            }
        }

        // These transformations must be done post-offsets
        trans *= agg::trans_affine_scaling(1.0, -1.0);
        trans *= agg::trans_affine_translation(0.0, (double)height);

        if (Nfacecolors) {
            typename ColorArray::sub_t facecolor = facecolors[i % Nfacecolors];
            face.second = agg::rgba(facecolor(0), facecolor(1), facecolor(2), facecolor(3));
        }

        if (Nedgecolors) {
            typename ColorArray::sub_t edgecolor = edgecolors[i % Nedgecolors];
            gc.color = agg::rgba(edgecolor(0), edgecolor(1), edgecolor(2), edgecolor(3));

            if (Nlinewidths) {
                gc.linewidth = linewidths(i % Nlinewidths);
            } else {
                gc.linewidth = 1.0;
            }
            if (Nlinestyles) {
                gc.dashes = linestyles[i % Nlinestyles];
            }
        }

        bool do_clip = !face.first && !gc.has_hatchpath() && !has_curves;

        if (check_snap) {
            gc.isaa = antialiaseds(i % Naa);

            transformed_path_t tpath(path, trans);
            nan_removed_t nan_removed(tpath, true, has_curves);
            clipped_t clipped(nan_removed, do_clip, width, height);
            snapped_t snapped(
                clipped, gc.snap_mode, path.total_vertices(), points_to_pixels(gc.linewidth));
            if (has_curves) {
                snapped_curve_t curve(snapped);
                _draw_path(curve, has_clippath, face, gc);
            } else {
                _draw_path(snapped, has_clippath, face, gc);
            }
        } else {
            gc.isaa = antialiaseds(i % Naa);

            transformed_path_t tpath(path, trans);
            nan_removed_t nan_removed(tpath, true, has_curves);
            clipped_t clipped(nan_removed, do_clip, width, height);
            if (has_curves) {
                curve_t curve(clipped);
                _draw_path(curve, has_clippath, face, gc);
            } else {
                _draw_path(clipped, has_clippath, face, gc);
            }
        }
    }
}

template <class PathGenerator,
          class TransformArray,
          class OffsetArray,
          class ColorArray,
          class LineWidthArray,
          class AntialiasedArray>
inline void RendererAgg::draw_path_collection(GCAgg &gc,
                                              agg::trans_affine &master_transform,
                                              PathGenerator &path,
                                              TransformArray &transforms,
                                              OffsetArray &offsets,
                                              agg::trans_affine &offset_trans,
                                              ColorArray &facecolors,
                                              ColorArray &edgecolors,
                                              LineWidthArray &linewidths,
                                              DashesVector &linestyles,
                                              AntialiasedArray &antialiaseds,
                                              e_offset_position offset_position)
{
    _draw_path_collection_generic(gc,
                                  master_transform,
                                  gc.cliprect,
                                  gc.clippath.path,
                                  gc.clippath.trans,
                                  path,
                                  transforms,
                                  offsets,
                                  offset_trans,
                                  facecolors,
                                  edgecolors,
                                  linewidths,
                                  linestyles,
                                  antialiaseds,
                                  offset_position,
                                  1,
                                  1);
}

template <class CoordinateArray>
class QuadMeshGenerator
{
    unsigned m_meshWidth;
    unsigned m_meshHeight;
    CoordinateArray m_coordinates;

    class QuadMeshPathIterator
    {
        unsigned m_iterator;
        unsigned m_m, m_n;
        const CoordinateArray *m_coordinates;

      public:
        QuadMeshPathIterator(unsigned m, unsigned n, const CoordinateArray *coordinates)
            : m_iterator(0), m_m(m), m_n(n), m_coordinates(coordinates)
        {
        }

      private:
        inline unsigned vertex(unsigned idx, double *x, double *y)
        {
            size_t m = m_m + ((idx & 0x2) >> 1);
            size_t n = m_n + (((idx + 1) & 0x2) >> 1);
            *x = (*m_coordinates)(n, m, 0);
            *y = (*m_coordinates)(n, m, 1);
            return (idx) ? agg::path_cmd_line_to : agg::path_cmd_move_to;
        }

      public:
        inline unsigned vertex(double *x, double *y)
        {
            if (m_iterator >= total_vertices()) {
                return agg::path_cmd_stop;
            }
            return vertex(m_iterator++, x, y);
        }

        inline void rewind(unsigned path_id)
        {
            m_iterator = path_id;
        }

        inline unsigned total_vertices()
        {
            return 5;
        }

        inline bool should_simplify()
        {
            return false;
        }
    };

  public:
    typedef QuadMeshPathIterator path_iterator;

    inline QuadMeshGenerator(unsigned meshWidth, unsigned meshHeight, CoordinateArray &coordinates)
        : m_meshWidth(meshWidth), m_meshHeight(meshHeight), m_coordinates(coordinates)
    {
    }

    inline size_t num_paths() const
    {
        return m_meshWidth * m_meshHeight;
    }

    inline path_iterator operator()(size_t i) const
    {
        return QuadMeshPathIterator(i % m_meshWidth, i / m_meshWidth, &m_coordinates);
    }
};

template <class CoordinateArray, class OffsetArray, class ColorArray>
inline void RendererAgg::draw_quad_mesh(GCAgg &gc,
                                        agg::trans_affine &master_transform,
                                        size_t mesh_width,
                                        size_t mesh_height,
                                        CoordinateArray &coordinates,
                                        OffsetArray &offsets,
                                        agg::trans_affine &offset_trans,
                                        ColorArray &facecolors,
                                        bool antialiased,
                                        ColorArray &edgecolors)
{
    QuadMeshGenerator<CoordinateArray> path_generator(mesh_width, mesh_height, coordinates);

    array::empty<double> transforms;
    array::scalar<double, 1> linewidths(points_to_pixels(gc.linewidth));
    array::scalar<uint8_t, 1> antialiaseds(antialiased);
    DashesVector linestyles;
    ColorArray *edgecolors_ptr = &edgecolors;

    if (edgecolors.size() == 0) {
        if (antialiased) {
            edgecolors_ptr = &facecolors;
        }
    }

    _draw_path_collection_generic(gc,
                                  master_transform,
                                  gc.cliprect,
                                  gc.clippath.path,
                                  gc.clippath.trans,
                                  path_generator,
                                  transforms,
                                  offsets,
                                  offset_trans,
                                  facecolors,
                                  *edgecolors_ptr,
                                  linewidths,
                                  linestyles,
                                  antialiaseds,
                                  OFFSET_POSITION_FIGURE,
                                  0,
                                  0);
}

template <class PointArray, class ColorArray>
inline void RendererAgg::_draw_gouraud_triangle(PointArray &points,
                                                ColorArray &colors,
                                                agg::trans_affine trans,
                                                bool has_clippath)
{
    typedef agg::rgba8 color_t;
    typedef agg::span_gouraud_rgba<color_t> span_gen_t;
    typedef agg::span_allocator<color_t> span_alloc_t;

    trans *= agg::trans_affine_scaling(1.0, -1.0);
    trans *= agg::trans_affine_translation(0.0, (double)height);

    double tpoints[3][2];

    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 2; ++j) {
            tpoints[i][j] = points(i, j);
        }
        trans.transform(&tpoints[i][0], &tpoints[i][1]);
    }

    span_alloc_t span_alloc;
    span_gen_t span_gen;

    span_gen.colors(agg::rgba(colors(0, 0), colors(0, 1), colors(0, 2), colors(0, 3)),
                    agg::rgba(colors(1, 0), colors(1, 1), colors(1, 2), colors(1, 3)),
                    agg::rgba(colors(2, 0), colors(2, 1), colors(2, 2), colors(2, 3)));
    span_gen.triangle(tpoints[0][0],
                      tpoints[0][1],
                      tpoints[1][0],
                      tpoints[1][1],
                      tpoints[2][0],
                      tpoints[2][1],
                      0.5);

    theRasterizer.add_path(span_gen);

    if (has_clippath) {
        typedef agg::pixfmt_amask_adaptor<pixfmt, alpha_mask_type> pixfmt_amask_type;
        typedef agg::renderer_base<pixfmt_amask_type> amask_ren_type;
        typedef agg::renderer_scanline_aa<amask_ren_type, span_alloc_t, span_gen_t>
        amask_aa_renderer_type;

        pixfmt_amask_type pfa(pixFmt, alphaMask);
        amask_ren_type r(pfa);
        amask_aa_renderer_type ren(r, span_alloc, span_gen);
        agg::render_scanlines(theRasterizer, scanlineAlphaMask, ren);
    } else {
        agg::render_scanlines_aa(theRasterizer, slineP8, rendererBase, span_alloc, span_gen);
    }
}

template <class PointArray, class ColorArray>
inline void RendererAgg::draw_gouraud_triangle(GCAgg &gc,
                                               PointArray &points,
                                               ColorArray &colors,
                                               agg::trans_affine &trans)
{
    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(gc.cliprect, theRasterizer);
    bool has_clippath = render_clippath(gc.clippath.path, gc.clippath.trans);

    if (points.dim(0) != 3 || points.dim(1) != 2) {
        throw "points must be a 3x2 array";
    }

    if (colors.dim(0) != 3 || colors.dim(1) != 4) {
        throw "colors must be a 3x4 array";
    }

    _draw_gouraud_triangle(points, colors, trans, has_clippath);
}

template <class PointArray, class ColorArray>
inline void RendererAgg::draw_gouraud_triangles(GCAgg &gc,
                                                PointArray &points,
                                                ColorArray &colors,
                                                agg::trans_affine &trans)
{
    theRasterizer.reset_clipping();
    rendererBase.reset_clipping(true);
    set_clipbox(gc.cliprect, theRasterizer);
    bool has_clippath = render_clippath(gc.clippath.path, gc.clippath.trans);

    if (points.dim(1) != 3 || points.dim(2) != 2) {
        throw "points must be a Nx3x2 array";
    }

    if (colors.dim(1) != 3 || colors.dim(2) != 4) {
        throw "colors must be a Nx3x4 array";
    }

    if (points.dim(0) != colors.dim(0)) {
        throw "points and colors arrays must be the same length";
    }

    for (int i = 0; i < points.dim(0); ++i) {
        typename PointArray::sub_t point = points[i];
        typename ColorArray::sub_t color = colors[i];

        _draw_gouraud_triangle(point, color, trans, has_clippath);
    }
}

template <class R>
void RendererAgg::set_clipbox(const agg::rect_d &cliprect, R &rasterizer)
{
    // set the clip rectangle from the gc

    if (cliprect.x1 != 0.0 || cliprect.y1 != 0.0 || cliprect.x2 != 0.0 || cliprect.y2 != 0.0) {
        rasterizer.clip_box(std::max(int(floor(cliprect.x1 + 0.5)), 0),
                            std::max(int(floor(height - cliprect.y1 + 0.5)), 0),
                            std::min(int(floor(cliprect.x2 + 0.5)), int(width)),
                            std::min(int(floor(height - cliprect.y2 + 0.5)), int(height)));
    } else {
        rasterizer.clip_box(0, 0, width, height);
    }
}

#endif
