#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# pylint: disable=low-comment-ratio, missing-license

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import List

import numpy as np
import pandas as pd

from .base import BaseEncoder
from ..helper import batching, cn_tokenizer, pooling_pd


class Word2VecEncoder(BaseEncoder):
    def __init__(self, model_dir,
                 skiprows: int = 1,
                 batch_size: int = 64,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_dir = model_dir
        self.skiprows = skiprows
        self.batch_size = batch_size
        self.pooling_strategy = pooling_strategy
        self.is_trained = True
        self._init_word_embedding()

    def _init_word_embedding(self):
        self.word2vec_df = pd.read_table(self.model_dir, sep=' ', quoting=3,
                                         header=None, skiprows=self.skiprows,
                                         index_col=0)
        self.word2vec_df = self.word2vec_df.astype(np.float32).dropna(axis=1).dropna(axis=0)
        self.empty = np.zeros([self.word2vec_df.shape[1]], dtype=np.float32)

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [cn_tokenizer.tokenize(sent) for sent in text]
        pooled_data = []

        for tokens in batch_tokens:
            try:
                _layer_data = self.word2vec_df.loc[tokens].dropna()
                _pooled = pooling_pd(_layer_data, self.pooling_strategy)
            except KeyError:
                _pooled = self.empty
            pooled_data.append(_pooled)
        return np.asarray(pooled_data, dtype=np.float32)

    def __getstate__(self):
        d = super().__getstate__()
        del d['word2vec_df']
        del d['empty']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._init_word_embedding()
