"""
  Copyright 2014 Google Inc. All rights reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

from fontTools.ttLib import TTFont
from dumper import Dumper
from base_fonter import BaseFonter
from compressor import Compressor
from glyf_serializer import GlyfSerializer
from cff_serializer import CffSerializer
from font_info import FontInfo
from base_header import BaseHeaderPrepare
import os


class Preprocess(object):
  """Generates base font and serialized glyf data, dumps cmap table"""

  def __init__(self, fontfile, folder,debug=False):
    self.debug = debug
    self.fontfile = fontfile
    self.folder = folder
    font = TTFont(self.fontfile,lazy=True)
    self.isCff = 'CFF ' in font

  def metadata(self):
    output = self.folder + '/metadata'
    font = TTFont(self.fontfile)
    metadata = {'numGlyphs': 0, 'has_hmtx': False, 'has_vmtx': False}
    metadata['numGlyphs'] = font['maxp'].numGlyphs
    if 'hmtx' in font:
      metadata['has_hmtx'] = True
      metadata['numberOfHMetrics'] = len(font['hmtx'].metrics)
    if 'vmtx' in font:
      metadata['has_vmtx'] = True
      metadata['numberOfVMetrics'] = len(font['vmtx'].metrics)

    dumper = Dumper(output)
    dumper.dumpObject(metadata)
    dumper.close()

  def base_font(self):
    output = self.folder + '/base'
    baseFonter = BaseFonter(self.fontfile)
    header_dict = FontInfo.getInformation(self.fontfile, FontInfo.TAGS.keys())
    bin_header = BaseHeaderPrepare.prepare(BaseFonter.BASE_VERSION, header_dict)
    baseFonter.base(output, bin_header)
    #compressor = Compressor(Compressor.LZMA_CMD)
    #compressor.compress(output, output + '.xz')
    #compressor = Compressor(Compressor.GZIP_CMD)
    #compressor.compress(output, output + '.gz')
    #if self.debug:
    #  print(os.path.getsize( output + '.gz'));

  def cmap_dump(self):
    font = TTFont(self.fontfile)
    #TODO(ahmetcelik) cmap in format 12 should be used if it exists
    cmapTable = font['cmap'].getcmap(3, 10)
    if not cmapTable:
      cmapTable = font['cmap'].getcmap(3, 1)
    assert cmapTable,'Unicode cmap table required'
    cmap = cmapTable.cmap  # unicode table
 

    codepoints = []
    glyphs = []

    for code, name in cmap.iteritems():
      id = font.getGlyphID(name)
      glyphs.append(id)
      codepoints.append(code)
      if self.debug:
        print id,name,code
    font.close()

    cp_dumper = Dumper(self.folder + '/codepoints')
    cp_dumper.dump_array(codepoints, 'I', '>')
    cp_dumper.close()

    gid_dumper = Dumper(self.folder + '/gids')
    gid_dumper.dump_array(glyphs, 'H', '>')
    gid_dumper.close()
    
  def serial_glyphs(self):
    if self.isCff:
      self._serial_Cff()
    else:
      self._serial_Glyf()
    

  def _serial_Glyf(self):
    glyfSerializer = GlyfSerializer(self.fontfile)
    glyfSerializer.prepare_glyf()
    glyfSerializer.serialize_glyf(
        self.folder + '/glyph_table', self.folder + '/glyph_data')
    
  def _serial_Cff(self):
    cffSerializer = CffSerializer(self.fontfile)
    cffSerializer.prepare_cff()
    cffSerializer.serialize_cff(
        self.folder + '/glyph_table', self.folder + '/glyph_data')
    cffSerializer.close()
