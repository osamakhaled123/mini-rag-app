from string import Template

system_prompt = Template("\n".join([
    "you are an assisstant to generate a response to the user.", 
    "you will be provided by a set of documents associated with the user's query.",
    "you have to generate a response to the user's query based on the documents provided.",
    "Ignore documents that are not relevant to the user's query.",
    "you can apologize to the user if you are not able to generate a response.",
    "you have to generate a response in the same language as the user's query.",
    "Be polite and respectful to the user.",
    "Be precise and concise in your generated response.",
    "Avoid unnecessary information."]))

document_prompt = Template("\n".join([
    "## Document No: $doc_num",
    "### Content: $chunk_text"]))

footer_prompt = Template("\n".join([
    "Based only on the above documents, generate an answer to the user's query.",
    "### Query:", 
    "$query",
    "",
    "## Answer: "
]))