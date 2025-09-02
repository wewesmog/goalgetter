import os

from typing import List, Dict, Any, Optional, TypedDict, Union
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
import requests
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
# ToolExecutor is not available in current langgraph version
# Use ToolNode instead if needed
# from langgraph.prebuilt import ToolNode
from psycopg2.extras import Json, RealDictCursor
from google.generativeai import GenerativeModel
import numpy as np
from openai import OpenAI
#from tavily import TavilyClient
from .logger_setup import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger()


def get_postgres_connection(table_name: str = None):
    """
    Establish and return a connection to the PostgreSQL database using Neon.
    Supports both connection string and individual parameter configurations.
    
    :param table_name: Name of the table to interact with (optional)
    :return: Connection object
    """
    # First try to use DATABASE_URL (Neon connection string)
    database_url = os.getenv("DATABASE_URL")
    
    if database_url and "neon.tech" in database_url:
        try:
            # Clean the DATABASE_URL by removing unsupported parameters
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            # Parse the URL
            parsed = urlparse(database_url)
            
            # Remove problematic query parameters that Neon doesn't support
            query_params = parse_qs(parsed.query)
            problematic_params = ['search_path', 'options', 'sslmode']
            
            for param in problematic_params:
                if param in query_params:
                    del query_params[param]
                    logger.info(f"Removed unsupported parameter: {param}")
            
            # Rebuild the URL without problematic parameters
            clean_query = urlencode(query_params, doseq=True)
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
            
            # Use cleaned connection string
            conn = psycopg2.connect(clean_url)
            logger.info("Successfully connected to Neon database using cleaned connection string")
            return conn
        except Exception as e:
            logger.warning(f"Failed to connect using DATABASE_URL: {e}")
            logger.info("Falling back to individual parameters...")
    elif database_url:
        logger.info("DATABASE_URL found but not a Neon URL, using individual parameters...")
    
    # Fallback to individual parameters (for backward compatibility)
    db_host = os.getenv("PGHOST")  # Host from connection string
    db_password = os.getenv("PGPASSWORD")  # Password from connection string
    db_port = os.getenv("PGPORT", "5432")  # Port from connection string, default to 5432
    db_name = os.getenv("PGDATABASE")  # Database name from connection string
    db_user = os.getenv("PGUSER")  # User from connection string

    if not all([db_host, db_password, db_user, db_name]):
        error_msg = "Missing required database credentials in environment variables. Need either DATABASE_URL or individual PGHOST, PGPASSWORD, PGUSER, PGDATABASE"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Direct PostgreSQL connection to Neon database
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        logger.info(f"Successfully connected to Neon database: {db_name}")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Unable to connect to database. Error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while connecting to database: {e}")
        raise

