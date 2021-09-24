#!/usr/bin/env bash

function main {
  local start=$(date +%s)
  local message=''
  local min_commits=20
  local max_commits=30
  local invert=0
  local preview=0

  while [[ $# > 0 ]]; do
    case "$1" in
      -c|--min-commits)
        if [[ $# < 2 ]]; then
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

      -h|--help)
        usage
        exit 0
      ;;

      -i|--invert)
        invert=1
      ;;

      -m|--message)
        if [[ $# < 2 ]]; then
          usage
          exit 1
        fi

        message="$2"
        shift
      ;;

      -p|--preview)
        preview=1
      ;;

      -s|--start)
        if [[ $# < 2 ]]; then
          usage
          exit 1
        fi

        start="$2"
        shift
      ;;

      *)
        1>&2 echo 'Unknown option '"$1"
        usage
        exit 1
      ;;
    esac

    shift
  done

  if (( $min_commits > $max_commits )); then
    1>&2 echo "MIN_COMMITS ($min_commits) cannot be more than MAX_COMMITS ($max_commits)"
    usage
    exit 1
  fi

  if [[ -z "$message" ]]; then
    1>&2 echo 'Missing required MESSAGE'
    usage
    exit 1
  fi

  local text="$(echo "$message" | tr a-z A-Z | tr -d -c 'A-Z ')"

  local font=()
  while IFS= read line; do
    font+=("$line")
  done < font.txt

  local grid=()
  for row in $(seq 0 6); do
    local row_text="."

    for (( i=0; i<${#text}; i++ )); do
      local char="${text:$i:1}"

      if [[ "$char" == " " ]]; then
        row_text="${row_text}..."
        continue
      fi

      local num=$(printf '%d' "'$char")
      num=$(( $num - 65 ))
      local font_index=$(( $num * 7 + $row ))
      row_text="${row_text}${font[$font_index]}."
    done

    grid+=("$row_text")
  done

  local beginning="$(date --date="@$start" '+%Y-%m-%d 12:00:00 %z')"
  beginning="$(date --date="$beginning -$(date --date="@$start" +%u) day -51 week")"

  echo "Starting on $beginning"

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

  local length=$(( ${#grid[0]} * ${#grid[@]} ))
  for (( day=0; day<$length; day++ )); do
    local y=$(( $day % 7 ))
    local x=$(( $day / 7 ))
    local row="${grid[$y]}"
    local char="${row:$x:1}"

    if [[ $invert == 0 ]]; then
      if [[ "$char" == '.' ]]; then
        continue
      fi
    else
      if [[ "$char" != '.' ]]; then
        continue
      fi
    fi

    local the_date="$(date --date="$beginning +$day day" "+%Y-%m-%d %H:%M:%S")"
    local commits_diff=$(( $max_commits - $min_commits + 1 ))
    local num_commits=$(( $min_commits + $RANDOM % $commits_diff ))

    for (( i=0; i<$num_commits; i++ )); do
      git commit --allow-empty --date="$the_date" --message "$the_date" > /dev/null
    done
  done
}

function usage {
  echo 'Usage:'
  echo '  ./main.sh [-c MIN_COMMITS] [-C MAX_COMMITS] [-p] [-i] [-s START] -m MESSAGE'
  echo '  ./main.sh -h'
  echo
  echo 'Options:'
  echo -e '  -c|--min-commits\tThe minimum commits for a day'
  echo -e '  -C|--max-commits\tThe maxmimum commits for a day'
  echo -e '  -h|--help\t\tShow this help message'
  echo -e '  -i|--invert\t\tInvert the text to be light text on dark background'
  echo -e '  -m|--message\t\tThe message to use'
  echo -e '  -p|--preview\t\tPreview the message'
  echo -e '  -s|--start\t\tThe date to start at, in unix epoch seconds'
}

main "$@"
