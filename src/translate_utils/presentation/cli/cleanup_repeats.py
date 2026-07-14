from translate_utils.infrastructure.logger import setup_logging
from translate_utils.services.cleanup_service import CleanupService
from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.presentation.cli.args import cleanup_repeats_parse_args
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanStrategy

LOGGER = setup_logging("CleanupRepeats")

def cleanup_repeats():
    parser = RpyTranslationParser()
    cleaner = CleanupService(parser)
    args = cleanup_repeats_parse_args()
    if not args.is_suitable_clean_method():
        LOGGER.warning(f"Clean method {args.clean_method} is not in {list(AVAILABLE_METHODS.keys())}, defaulting to 'only_comment'...")
    clean_method: CleanStrategy = AVAILABLE_METHODS.get(args.clean_method, AVAILABLE_METHODS["only_comment"])

    if args.filepaths is None:
        LOGGER.info("There is no filepath given")
    else:
        LOGGER.info(f"Loading and parsing: {args.filepaths}...")
        for filepath in args.filepaths:
            cleaner.clean_and_save(filepath=filepath, new_name=args.name, clean_method=clean_method)
            

if __name__ == "__main__":
    cleanup_repeats()