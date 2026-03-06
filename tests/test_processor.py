import os
import pytest
from unittest.mock import patch, MagicMock

import processor


def test_get_output_files_empty_dir(tmp_path):
    assert processor.get_output_files(str(tmp_path)) == []


def test_get_output_files_returns_all_files(tmp_path):
    a = tmp_path / 'a.epub'
    b = tmp_path / 'b.epub'
    a.write_text('a')
    b.write_text('b')
    # Force distinct mtimes so sort order is deterministic
    os.utime(str(a), (1000, 1000))
    os.utime(str(b), (2000, 2000))
    result = processor.get_output_files(str(tmp_path))
    assert len(result) == 2
    assert result[0].endswith('a.epub')
    assert result[1].endswith('b.epub')


def test_get_output_files_ignores_subdirectories(tmp_path):
    (tmp_path / 'file.epub').write_text('x')
    (tmp_path / 'subdir').mkdir()
    result = processor.get_output_files(str(tmp_path))
    assert len(result) == 1


def test_move_output_file_renames_kepub_epub(tmp_path):
    src = tmp_path / 'src'
    dst = tmp_path / 'dst'
    src.mkdir()
    src_file = src / 'mycomic.kepub.epub'
    src_file.write_text('data')
    processor.move_output_file(str(src_file), str(dst))
    assert (dst / 'mycomic.kepub').exists()
    assert not src_file.exists()


def test_move_output_file_leaves_regular_epub_alone(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    src_file = src / 'mybook.epub'
    src_file.write_text('data')
    processor.move_output_file(str(src_file), str(tmp_path / 'dst'))
    assert (tmp_path / 'dst' / 'mybook.epub').exists()


def test_move_output_file_creates_target_dir(tmp_path):
    src = tmp_path / 'file.epub'
    src.write_text('data')
    deep_dst = tmp_path / 'deep' / 'nested' / 'dir'
    processor.move_output_file(str(src), str(deep_dst))
    assert (deep_dst / 'file.epub').exists()


def test_prune_empty_dirs_removes_nested(tmp_path):
    nested = tmp_path / 'a' / 'b' / 'c'
    nested.mkdir(parents=True)
    fake_file = nested / 'file.epub'
    processor.prune_empty_dirs(str(fake_file), str(tmp_path))
    assert not (tmp_path / 'a').exists()


def test_prune_empty_dirs_does_not_remove_base(tmp_path):
    sub = tmp_path / 'sub'
    sub.mkdir()
    fake_file = sub / 'file.epub'
    processor.prune_empty_dirs(str(fake_file), str(tmp_path))
    assert tmp_path.exists()


def test_prune_empty_dirs_stops_at_nonempty_parent(tmp_path):
    nested = tmp_path / 'a' / 'b'
    nested.mkdir(parents=True)
    # Put a file in 'a' so it can't be removed
    (tmp_path / 'a' / 'keep.txt').write_text('x')
    fake_file = nested / 'file.epub'
    processor.prune_empty_dirs(str(fake_file), str(tmp_path))
    assert not (tmp_path / 'a' / 'b').exists()
    assert (tmp_path / 'a').exists()


def test_process_file_flags_failed_when_no_output(tmp_path):
    # KCC exits 0 but produces no output files — source must be renamed .failed,
    # not left in place to be retried on the next scan.
    comics_in = tmp_path / 'comics_in'
    comics_in.mkdir()
    src = comics_in / 'test.cbz'
    src.write_bytes(b'fake cbz')

    mock_config = {k: v for k, v in processor.DEFAULT_CONFIG.items()} if hasattr(processor, 'DEFAULT_CONFIG') else {
        'kcc_profile': 'KoLC', 'kcc_format': 'EPUB', 'kcc_splitter': '1',
        'kcc_cropping': '2', 'kcc_croppingpower': '1.0', 'kcc_croppingminimum': '1',
        'kcc_batchsplit': '0', 'kcc_gamma': '0', 'kcc_manga_style': False,
        'kcc_hq': False, 'kcc_two_panel': False, 'kcc_webtoon': False,
        'kcc_blackborders': True, 'kcc_whiteborders': False, 'kcc_forcecolor': True,
        'kcc_colorautocontrast': True, 'kcc_colorcurve': False, 'kcc_stretch': True,
        'kcc_upscale': False, 'kcc_nosplitrotate': False, 'kcc_rotate': False,
        'kcc_nokepub': False, 'kcc_metadatatitle': False, 'kcc_author': '',
        'kcc_customwidth': '', 'kcc_customheight': '',
    }

    with patch.object(processor, 'COMICS_IN', str(comics_in)), \
         patch.object(processor, 'COMICS_OUT', str(tmp_path / 'comics_out')), \
         patch('processor.load_config', return_value=mock_config), \
         patch('processor.wait_for_file_ready', return_value=True), \
         patch('processor._run_conversion', return_value=None):
        # _run_conversion succeeds (no exception) but writes nothing to temp_out
        processor.process_file(str(src), 'comic')

    assert not src.exists(), "source file should have been removed or renamed"
    assert (comics_in / 'test.cbz.failed').exists(), "source should be renamed .failed when no output produced"
