use wasm_bindgen::prelude::*;

#[wasm_bindgen]
extern "C" {
    fn alert(input: &str);

    #[wasm_bindgen(js_namespace = console)]
    fn log(input: &str);
}


macro_rules! console_logger {
    ($($val:tt)*) => {
        log(format_args!($($val)*).to_string().as_str())
    };
}


#[wasm_bindgen]
pub fn create_token_mint (tokenName: &str, tokenSymbol: &str, tokenUri: &str){
    log(&format!("Creating token mint: {} {} {}", tokenName, tokenSymbol, tokenUri));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
    }
}
