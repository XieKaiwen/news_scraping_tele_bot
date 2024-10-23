from sqlalchemy.exc import IntegrityError, DatabaseError, NoResultFound, OperationalError

def handle_data_mutation_error(error: Exception) -> str:
    """
    Handles errors that occur during data mutation (e.g., create, update, delete).
    
    Args:
        error (Exception): The exception that was raised during the mutation operation.
    
    Returns:
        str: A user-friendly error message.
    """
    if isinstance(error, IntegrityError):
        # Handle constraint violation (e.g., unique constraint, foreign key constraint)
        return "There was an integrity error. This could be due to a duplicate entry or invalid reference."
    
    elif isinstance(error, DatabaseError):
        # Handle general database errors
        return "A database error occurred while processing your request. Please try again later."
    
    elif isinstance(error, ValueError):
        # Handle validation or value errors
        return "Invalid data was provided. Please check your input and try again."
    
    else:
        # General fallback for any other unhandled exceptions
        return f"An unexpected error occurred: {str(error)}"

from sqlalchemy.exc import NoResultFound, OperationalError

def handle_data_fetching_error(error: Exception) -> str:
    """
    Handles errors that occur during data fetching (e.g., querying the database).
    
    Args:
        error (Exception): The exception that was raised during the fetching operation.
    
    Returns:
        str: A user-friendly error message.
    """
    if isinstance(error, NoResultFound):
        # Handle case where no data is found
        return "No data found for the requested query. Please check your request and try again."
    
    elif isinstance(error, OperationalError):
        # Handle database connectivity or operational errors
        return "There was an error connecting to the database. Please try again later."
    
    elif isinstance(error, TimeoutError):
        # Handle timeout errors
        return "The request timed out. Please try again later."
    
    else:
        # General fallback for any other unhandled exceptions
        return f"An unexpected error occurred: {str(error)}"
