#!/usr/bin/env bash

function main {
  local start=$(date +%s)
  local message=''
  local min_commits=30
  local max_commits=35
  local invert=0
  local preview=0
  local dry_run=0

  while [[ $# > 0 ]]; do
    case "$1" in
      -c|--min-commits)
        if [[ $# < 2 ]]; then
          1>&2 echo 'Missing required argument MIN_COMMITS'
          usage
          exit 1
        fi

        if ! [[ "$2" =~ ^[0-9]+$ ]]; then
          1>&2 echo 'MIN_COMMITS must be a number'
          usage
          exit 1
        fi

        if (( "$2" < 1 )); then
          1>&2 echo 'MIN_COMMITS must be at least 1'
          usage
          exit 1
        fi

        min_commits="$2"
        shift
      ;;

      -C|--max-commits)
        if [[ $# < 2 ]]; then
          1>&2 echo 'Missing required argument MAX_COMMITS'
          usage
          exit 1
        fi

        if ! [[ "$2" =~ ^[0-9]+$ ]]; then
          1>&2 echo 'MAX_COMMITS must be a number'
          usage
          exit 1
        fi

        if (( "$2" < 1 )); then
          1>&2 echo 'MAX_COMMITS must be at least 1'
          usage
          exit 1
        fi

        max_commits="$2"
        shift
      ;;

      -d|--dry-run)
        dry_run=1
      ;;

      -h|--help)
        usage
        exit 0
      ;;

      -i|--invert)
        invert=1
      ;;

      -p|--preview)
        preview=1
      ;;

      -s|--start)
        if [[ $# < 2 ]]; then
          1>&2 echo 'Missing required argument START'
          usage
          exit 1
        fi

        if ! [[ "$2" =~ ^[0-9]+$ ]]; then
          1>&2 echo 'START must be a number of seconds'
          usage
          exit 1
        fi

        start="$2"
        shift
      ;;

      --)
        message="${@:2}"
        shift $#
      ;;

      *)
        if [[ $# > 1 ]]; then
          1>&2 echo 'Unknown options'
          usage
          exit 1
        else
          message="$1"
        fi
      ;;
    esac

    shift
  done

  if [[ -z "$message" ]]; then
    1>&2 echo 'Missing required MESSAGE'
    usage
    exit 1
  fi

  if (( $min_commits > $max_commits )); then
    1>&2 echo "MIN_COMMITS ($min_commits) cannot be more than MAX_COMMITS ($max_commits)"
    usage
    exit 1
  fi

  local text="$(echo "$message" | tr -d -c ' -~')"
  local invalid="$(echo "$message" | tr -d ' -~')"

  if [[ -n "$invalid" ]]; then
    local formatted=()
    for (( i=0; i<${#invalid}; i++ )); do
      local char="${invalid:$i:1}"
      local char_num=$(printf %d "'$char")

      # unprintable chars convert to hex
      if (( $char_num < 32 )) || (( $char_num >= 127 )); then
        formatted+=("($(printf '0x%.2x' "'$char"))")
      else
        formatted+=("$char")
      fi
    done

    1>&2 echo "Unsupported characters in MESSAGE: ${formatted[@]}"
    exit 1
  fi

  local font_start=$(printf '%d' "' ") # start at space
  local font=()
  while IFS= read line; do
    if [[ -n "$line" ]]; then
      font+=("$line")
    fi
  done < font.txt

  local grid=()
  for row in $(seq 0 6); do
    local row_text="."

    for (( i=0; i<${#text}; i++ )); do
      local char="${text:$i:1}"
      local num=$(printf '%d' "'$char")
      num=$(( $num - $font_start ))
      local font_index=$(( $num * 7 + $row ))
      row_text="${row_text}${font[$font_index]}."
    done

    grid+=("$row_text")
  done

  local num_days=$(( ${#grid[0]} * ${#grid[@]} - 1 ))
  local beginning="$(date --date="@$start" '+%Y-%m-%d 12:00:00 %z')"
  beginning="$(date --date="$beginning -$(date --date="@$start" +%u) day -51 week")"
  local end="$(date --date="$beginning +$num_days day")"

  echo "Starting on $beginning"
  echo "Ending on   $end"

  if [[ $preview == 1 ]]; then
    for (( i=0; i<${#grid[@]}; i++ )); do
      local row="${grid[$i]}"

      if [[ $invert == 0 ]]; then
        echo "$row" | tr '.' ' '
      else
        echo "$row" | tr '#.' ' #'
      fi
    done

    exit 0
  fi

  for (( day=0; day<=$num_days; day++ )); do
    local y=$(( $day % 7 ))
    local x=$(( $day / 7 ))
    local row="${grid[$y]}"
    local char="${row:$x:1}"
    local the_date="$(date --date="$beginning +$day day" "+%Y-%m-%d %H:%M:%S")"

    echo -en "\r$the_date `progress $(( $day * 100 / $num_days ))`"

    if [[ $invert == 0 ]]; then
      if [[ "$char" == '.' ]]; then
        continue
      fi
    else
      if [[ "$char" != '.' ]]; then
        continue
      fi
    fi

    local commits_diff=$(( $max_commits - $min_commits + 1 ))
    local num_commits=$(( $min_commits + $RANDOM % $commits_diff ))

    for (( i=0; i<$num_commits; i++ )); do
      if [[ $dry_run == 0 ]]; then
        git commit --allow-empty --date="$the_date" --message "$the_date" > /dev/null
      fi
    done
  done

  echo -e "\r$the_date `progress 100`"
}

function progress {
  local percent="$1"

  local bar=""
  for (( i=1; i<=25; i++ )); do
    if (( $i * 4 <= $percent )); then
      bar="$bar="
    else
      bar="$bar "
    fi
  done

  echo "[$bar] $percent%"
}

function usage {
  echo 'Usage:'
  echo '  ./main.sh [-c MIN_COMMITS] [-C MAX_COMMITS] [-d] [-i] [-p] [-s START] MESSAGE'
  echo '  ./main.sh -h'
  echo
  echo 'Options:'
  echo -e '  -c|--min-commits\tThe minimum commits for a day'
  echo -e '  -C|--max-commits\tThe maxmimum commits for a day'
  echo -e '  -d|--dry-run\tDo not actually create the commits'
  echo -e '  -h|--help\t\tShow this help message'
  echo -e '  -i|--invert\t\tInvert the text to be light text on dark background'
  echo -e '  -p|--preview\t\tPreview the message'
  echo -e '  -s|--start\t\tThe date to start at, in unix epoch seconds'
}

main "$@"
