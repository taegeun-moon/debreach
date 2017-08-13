#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include "php.h"
#include "php_debreach.h"
#include "mod_debreach.h"
#include "SAPI.h"
#include "httpd.h"
#include "util_filter.h"
#include "string.h"

/* Terrible hack... but the only way for us 
 * to get server_context struct definition used by the PHP apache module */
typedef struct php_struct {
    int state;
    request_rec *r; 
    apr_bucket_brigade *brigade;
    /* stat structure of the current file */
    zend_stat_t finfo;
    /* Whether or not we've processed PHP in the output filters yet. */
    int request_processed;
    /* final content type */
    char *content_type;
} php_struct;

ZEND_BEGIN_ARG_INFO_EX(arginfo_debreach_taint_brs, 0, 0, 2)
	ZEND_ARG_INFO(0, br_start)
	ZEND_ARG_INFO(0, br_end)
ZEND_END_ARG_INFO()

static zend_function_entry debreach_functions[] = {
    PHP_FE(taint_brs, arginfo_debreach_taint_brs)
    {NULL, NULL, NULL}
};

zend_module_entry debreach_module_entry = {
#if ZEND_MODULE_API_NO >= 20010901
    STANDARD_MODULE_HEADER,
#endif
    PHP_DEBREACH_EXTNAME,
    debreach_functions,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
#if ZEND_MODULE_API_NO >= 20010901
    PHP_DEBREACH_VERSION,
#endif
    STANDARD_MODULE_PROPERTIES
};

#ifdef COMPILE_DL_DEBREACH
ZEND_GET_MODULE(debreach)
#endif

PHP_FUNCTION(taint_brs)
{
	php_struct *php_ctx;
	struct ap_filter_t *filter_chain = NULL;
	long start, end;
	char *note_val;

	if (zend_parse_parameters(ZEND_NUM_ARGS(), "ll", &start, &end) == FAILURE) {
		return;
	}

	php_ctx = SG(server_context);

	// find the debreach filter for this request
	filter_chain = php_ctx->r->output_filters;
	while (filter_chain != NULL) {
		if (strncmp(filter_chain->frec->name, debreachFilterName, 1024))
			break;
		filter_chain = filter_chain->next;
	}

	if (filter_chain == NULL)
		RETURN_STRING("Could not find "debreachFilterName" in filter chain");

	// we have the debreach filter in *filter_chain
	mod_debreach_taint_brs(filter_chain, start, end);

    RETURN_TRUE;
}
