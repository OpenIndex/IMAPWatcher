#!/usr/bin/env bash
#
# Copyright 2023 OpenIndex.de.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Run Python interpreter from virtual environment.
#

set -e
BASE_DIR="$( cd "$( dirname "$(realpath "${BASH_SOURCE[0]}")" )" && pwd )"
ENV_DIR="${BASE_DIR}/env"

if [ ! -d "${ENV_DIR}" ]; then
  echo "Virtual environment does not exist yet. Trying to create..."
  "${BASE_DIR}/init.sh"
fi

source "${ENV_DIR}/bin/activate"

if [ -z "${PYTHONPATH}" ]
then
  export PYTHONPATH="${BASE_DIR}/src"
else
  export PYTHONPATH="${BASE_DIR}/src:${PYTHONPATH}"
fi

#echo "running Python with ${PYTHONPATH}"
"${ENV_DIR}/bin/python" "$@"
deactivate
