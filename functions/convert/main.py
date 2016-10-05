# -*- coding: utf-8 -*-

# Method for converting USFM files to HTML

from __future__ import print_function, unicode_literals

import os
import tempfile
import transform_bible

from glob import glob

from general_tools.file_utils import add_contents_to_zip
from aws_tools.s3_handler import S3Handler

def log_message(log, message):
    print(message)
    log.append(message)


def error_message(errors, message):
    print(message)
    errors.append(message)


def warning_message(warnings, message):
    print(message)
    warnings.append(message)


def handle(event, context):
    log = []
    errors = []
    warnings = []

    if 'data' not in event:
        raise Exception('"data" was not in payload')
    data = event['data']

    if 'job' not in data:
        raise Exception('"job" was not in payload')
    job = data['job']
    
    if 'source' not in job:
        raise Exception('"source" was not in "job"')
    source = job['source']
    
    if 'resource_type' not in job:
        raise Exception ('"resource_type" was not in "job"')
    resource = job['resource_type']
    
    if 'cdn_bucket' not in job:
        raise Exception('"cdn_bucket" was not in "job"')
    cdn_bucket = job['cdn_bucket']
    
    if 'cdn_file' not in job:
        raise Exception('"cdn_file" was not in "job')
    cdn_file = job['cdn_file']
    
    print('source: ' + source)
    print('cdn_bucket: ' + cdn_bucket)
    print('cdn_file: ' + cdn_file)
    
    options = {
        'line_spacing': '120%'
    }
    
    if 'options' in job:
        options.update(job['options'])
    
    output_dir = os.path.join(tempfile.gettempdir(), context.aws_request_id)

    success = False
    try:
        if resource == 'bible' or resource == 'ulb' or resource == 'udb':
            converter = transform_bible.TransformBible(source, output_dir, options)
            try:
                converter.run()
            except Exception as e:
                error_message(errors, e.message)
            finally:
                log.extend(converter.log)
                errors.extend(converter.errors)
                warnings.extend(converter.warnings)
        else:
            raise Exception('Resource "{0}" not currently supported'.format(resource))

        zip_file = os.path.join(tempfile.gettempdir(), context.aws_request_id+'.zip')
        add_contents_to_zip(zip_file, output_dir)
        log_message(log, "Uploading {0} to {1}/{2}".format(os.path.basename(zip_file), cdn_bucket, cdn_file))
        cdn_handler = S3Handler(cdn_bucket)
        cdn_handler.upload_file(zip_file, cdn_file)
        log_message(log, "Upload was successful.")
        success = True
    except Exception as e:
        error_message(errors, e.message)

    return {
        'log': log,
        'errors': errors,
        'warnings': warnings,
        'success': success
    }
